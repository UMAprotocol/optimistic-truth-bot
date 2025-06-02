"""Manager for orchestrating the PolyMarket Oracle agentic system."""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from rich.console import Console
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    class Console:
        def __init__(self):
            pass

from agents import Runner, RunResult, custom_span, gen_trace_id, trace

from .agents.router_agent import RoutingDecision, router_agent
from .agents.perplexity_solver import PerplexityResult, perplexity_solver
from .agents.code_runner_solver import CodeRunnerResult, code_runner_solver
from .agents.overseer_agent import OverseerDecision, overseer_agent


def _load_api_keys_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load API keys configuration from JSON file."""
    if config_path is None:
        config_path = "../api_keys_config.json"
    
    try:
        config_path = Path(config_path)
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load API keys config from {config_path}: {e}")
    
    return {"data_sources": []}


class PolyMarketOracleManager:
    """
    Orchestrates the full PolyMarket Oracle flow: routing, solving, and oversight.
    """

    def __init__(self, verbose: bool = True, api_keys_config_path: Optional[str] = None):
        self.console = Console() if HAS_RICH else None
        self.verbose = verbose
        self.api_keys_config = _load_api_keys_config(api_keys_config_path)
        self.max_routing_attempts = 3
        self.max_solver_attempts = 2

    async def process_proposal(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single PolyMarket proposal through the full pipeline.
        
        Args:
            proposal_data: The proposal data loaded from JSON file
            
        Returns:
            Dictionary containing the final result and processing details
        """
        trace_id = gen_trace_id()
        start_time = time.time()
        
        # Initialize journey tracking
        journey = []
        step_counter = 1
        
        with trace("PolyMarket Oracle processing", trace_id=trace_id):
            if self.verbose:
                print(f"🔮 Processing proposal: {proposal_data.get('query_id', 'unknown')}")
                print(f"📊 View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            
            # Extract the market question from ancillary_data
            market_question = self._extract_market_question(proposal_data)
            
            # Main processing loop with retry logic
            final_recommendation = None
            excluded_solvers = []
            routing_phase = 1
            
            for routing_attempt in range(1, self.max_routing_attempts + 1):
                if self.verbose:
                    print(f"🔄 Routing attempt {routing_attempt}/{self.max_routing_attempts}")
                
                # Step 1: Route the question to appropriate solver(s)
                routing_decision, routing_step = await self._route_question_with_tracking(
                    market_question, step_counter, routing_attempt, routing_phase, excluded_solvers
                )
                journey.append(routing_step)
                step_counter += 1
                
                # Step 2: Execute the selected solver(s)
                solver_results = []
                for solver_name in routing_decision.solvers:
                    for attempt in range(1, self.max_solver_attempts + 1):
                        solver_result, solver_step = await self._execute_solver_with_tracking(
                            solver_name, market_question, proposal_data, 
                            step_counter, attempt, routing_phase
                        )
                        journey.append(solver_step)
                        step_counter += 1
                        
                        # Step 3: Overseer evaluation
                        overseer_result, overseer_step = await self._evaluate_solver_with_tracking(
                            solver_name, solver_result, market_question, proposal_data,
                            step_counter, attempt, routing_phase
                        )
                        journey.append(overseer_step)
                        step_counter += 1
                        
                        # Check if overseer is satisfied
                        if overseer_result.verdict == "SATISFIED":
                            final_recommendation = overseer_result.final_recommendation
                            break
                        elif overseer_result.verdict == "DEFAULT_TO_P4":
                            excluded_solvers.append(solver_name)
                            break
                        # If RETRY, continue to next attempt
                    
                    if final_recommendation:
                        break
                
                if final_recommendation:
                    break
                    
                # If we reach here, check if we should reroute
                if routing_attempt < self.max_routing_attempts:
                    routing_phase += 1
                    if self.verbose:
                        print(f"🔀 Re-routing needed, excluded solvers: {excluded_solvers}")
            
            # Step 4: Compile final result
            final_result = self._compile_final_result_with_journey(
                proposal_data,
                journey,
                final_recommendation or "p4",
                start_time
            )
            
            if self.verbose:
                print(f"✅ Final recommendation: {final_result.get('recommendation', 'unknown')}")
            
            return final_result

    def _extract_market_question(self, proposal_data: Dict[str, Any]) -> str:
        """Extract the market question from proposal ancillary data."""
        ancillary_data = proposal_data.get('ancillary_data', '')
        
        # Extract the question and description
        question_parts = []
        
        # Look for title
        if 'title:' in ancillary_data:
            title_start = ancillary_data.find('title:') + 6
            title_end = ancillary_data.find(',', title_start)
            if title_end == -1:
                title_end = ancillary_data.find('\n', title_start)
            if title_end != -1:
                title = ancillary_data[title_start:title_end].strip()
                question_parts.append(f"Title: {title}")
        
        # Look for description
        if 'description:' in ancillary_data:
            desc_start = ancillary_data.find('description:') + 12
            desc_end = ancillary_data.find('res_data:', desc_start)
            if desc_end == -1:
                desc_end = len(ancillary_data)
            description = ancillary_data[desc_start:desc_end].strip()
            question_parts.append(f"Description: {description}")
        
        # Add resolution conditions
        resolution_conditions = proposal_data.get('resolution_conditions', '')
        if resolution_conditions:
            question_parts.append(f"Resolution: {resolution_conditions}")
        
        # Add market pricing context
        proposed_price = proposal_data.get('proposed_price', 0)
        proposed_outcome = proposal_data.get('proposed_price_outcome', '')
        if proposed_outcome:
            question_parts.append(f"Current proposal: {proposed_outcome} (price: {proposed_price})")
        
        # Add tags for context
        tags = proposal_data.get('tags', [])
        if tags:
            question_parts.append(f"Tags: {', '.join(tags)}")
        
        return '\n\n'.join(question_parts)

    async def _route_question_with_tracking(
        self, 
        market_question: str, 
        step: int, 
        attempt: int, 
        routing_phase: int,
        excluded_solvers: List[str]
    ) -> tuple[RoutingDecision, Dict[str, Any]]:
        """Route the question with tracking."""
        start_time = time.time()
        
        # Enhance the router prompt with API config and exclusions
        enhanced_prompt = self._enhance_router_prompt(market_question, excluded_solvers)
        
        if self.verbose:
            print("🔄 Routing question to appropriate solver(s)...")
        
        with custom_span("Route question"):
            result = await Runner.run(router_agent, enhanced_prompt)
            routing_decision = result.final_output_as(RoutingDecision)
        
        end_time = time.time()
        
        # Create tracking step
        step_data = {
            "step": step,
            "actor": "router",
            "action": "route",
            "attempt": attempt,
            "routing_phase": routing_phase,
            "prompt": enhanced_prompt,
            "response": {
                "solvers": routing_decision.solvers,
                "reason": routing_decision.reason,
                "multi_solver_strategy": routing_decision.multi_solver_strategy
            },
            "timestamp": end_time,
            "start_time": start_time,
            "end_time": end_time,
            "duration_seconds": int(end_time - start_time),
            "metadata": {
                "available_solvers": ["perplexity", "code_runner"],
                "excluded_solvers": excluded_solvers
            },
            "full_response": str(result.final_output)
        }
        
        return routing_decision, step_data

    def _enhance_router_prompt(self, market_question: str, excluded_solvers: List[str]) -> str:
        """Enhance router prompt with API configuration and exclusions."""
        prompt = f"Market Question:\n{market_question}\n\n"
        
        # Add API configuration info
        if self.api_keys_config.get("data_sources"):
            prompt += "Available API Data Sources:\n"
            for source in self.api_keys_config["data_sources"]:
                prompt += f"- {source['name']} ({source['category']}): {source['description']}\n"
        
        # Add exclusions
        if excluded_solvers:
            prompt += f"\nExcluded solvers (due to previous failures): {', '.join(excluded_solvers)}\n"
        
        return prompt

    async def _route_question(self, market_question: str) -> RoutingDecision:
        """Route the question to appropriate solver(s)."""
        if self.verbose:
            print("🔄 Routing question to appropriate solver(s)...")
        
        with custom_span("Route question"):
            result = await Runner.run(router_agent, market_question)
            return result.final_output_as(RoutingDecision)

    async def _execute_solver_with_tracking(
        self,
        solver_name: str,
        market_question: str,
        proposal_data: Dict[str, Any],
        step: int,
        attempt: int,
        routing_phase: int
    ) -> tuple[Any, Dict[str, Any]]:
        """Execute a single solver with tracking."""
        start_time = time.time()
        
        if self.verbose:
            print(f"🧠 Executing {solver_name} solver (attempt {attempt})")
        
        try:
            if solver_name == "perplexity":
                result = await self._run_perplexity_solver(market_question)
                solver_result = result
            elif solver_name == "code_runner":
                result = await self._run_code_runner_solver(market_question, proposal_data)
                solver_result = result
            else:
                raise ValueError(f"Unknown solver: {solver_name}")
                
        except Exception as e:
            if self.verbose:
                print(f"❌ Error in {solver_name}: {str(e)}")
            solver_result = type('ErrorResult', (), {
                'recommendation': 'p4',
                'reasoning': f"Error executing solver: {str(e)}",
                'confidence': 'Low'
            })()
        
        end_time = time.time()
        
        # Create tracking step
        step_data = {
            "step": step,
            "actor": solver_name,
            "action": "solve",
            "attempt": attempt,
            "routing_phase": routing_phase,
            "prompt": market_question,
            "response": {
                "recommendation": getattr(solver_result, 'recommendation', 'p4'),
                "reasoning": getattr(solver_result, 'reasoning', 'No reasoning provided'),
                "confidence": getattr(solver_result, 'confidence', 'Unknown')
            },
            "timestamp": end_time,
            "start_time": start_time,
            "end_time": end_time,
            "duration_seconds": int(end_time - start_time),
            "status": "completed" if hasattr(solver_result, 'recommendation') else "error",
            "metadata": {
                "solver_type": solver_name
            }
        }
        
        return solver_result, step_data

    async def _evaluate_solver_with_tracking(
        self,
        solver_name: str,
        solver_result: Any,
        market_question: str,
        proposal_data: Dict[str, Any],
        step: int,
        attempt: int,
        routing_phase: int
    ) -> tuple[OverseerDecision, Dict[str, Any]]:
        """Evaluate solver result with overseer and tracking."""
        start_time = time.time()
        
        if self.verbose:
            print(f"👁️  Evaluating {solver_name} result with overseer...")
        
        # Prepare evaluation context
        evaluation_context = self._prepare_overseer_context(
            market_question, solver_name, solver_result, proposal_data
        )
        
        with custom_span("Overseer evaluation"):
            result = await Runner.run(overseer_agent, evaluation_context)
            overseer_decision = result.final_output_as(OverseerDecision)
        
        end_time = time.time()
        
        # Create tracking step
        step_data = {
            "step": step,
            "actor": "overseer",
            "action": "evaluate",
            "attempt": attempt,
            "routing_phase": routing_phase,
            "prompt": evaluation_context,
            "response": {
                "verdict": overseer_decision.verdict,
                "require_rerun": overseer_decision.require_rerun,
                "reason": overseer_decision.reason,
                "final_recommendation": overseer_decision.final_recommendation
            },
            "verdict": overseer_decision.verdict.lower(),
            "critique": overseer_decision.critique,
            "market_alignment": overseer_decision.market_alignment,
            "require_rerun": overseer_decision.require_rerun,
            "reason": overseer_decision.reason,
            "timestamp": end_time,
            "start_time": start_time,
            "end_time": end_time,
            "duration_seconds": int(end_time - start_time),
            "status": "completed",
            "metadata": {
                "evaluated_step": step - 1,
                "evaluated_actor": solver_name
            }
        }
        
        return overseer_decision, step_data

    def _prepare_overseer_context(
        self,
        market_question: str,
        solver_name: str,
        solver_result: Any,
        proposal_data: Dict[str, Any]
    ) -> str:
        """Prepare context for overseer evaluation."""
        context = f"""Market Question:
{market_question}

Solver: {solver_name}
Recommendation: {getattr(solver_result, 'recommendation', 'p4')}
Reasoning: {getattr(solver_result, 'reasoning', 'No reasoning provided')}
Confidence: {getattr(solver_result, 'confidence', 'Unknown')}
"""
        
        # Add market pricing context
        tokens = proposal_data.get('tokens', [])
        if tokens:
            context += "\nMarket Pricing Context:\n"
            for token in tokens:
                context += f"- {token.get('outcome', 'Unknown')}: {token.get('price', 0):.3f}\n"
        
        # Add resolution conditions
        resolution_conditions = proposal_data.get('resolution_conditions', '')
        if resolution_conditions:
            context += f"\nResolution Conditions:\n{resolution_conditions}\n"
        
        return context

    async def _execute_solvers(
        self, 
        market_question: str, 
        solvers: List[str],
        proposal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the selected solver(s)."""
        if self.verbose:
            print(f"🧠 Executing solver(s): {', '.join(solvers)}")
        
        results = {}
        
        with custom_span("Execute solvers"):
            # Execute solvers in parallel if multiple
            tasks = []
            
            for solver_name in solvers:
                if solver_name == "perplexity":
                    tasks.append(self._run_perplexity_solver(market_question))
                elif solver_name == "code_runner":
                    tasks.append(self._run_code_runner_solver(market_question, proposal_data))
                else:
                    if self.verbose:
                        print(f"⚠️  Unknown solver: {solver_name}")
            
            # Wait for all solver tasks to complete
            if tasks:
                solver_outputs = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, output in enumerate(solver_outputs):
                    solver_name = solvers[i] if i < len(solvers) else f"solver_{i}"
                    
                    if isinstance(output, Exception):
                        if self.verbose:
                            print(f"❌ Error in {solver_name}: {str(output)}")
                        results[solver_name] = {
                            "error": str(output),
                            "recommendation": "p4"
                        }
                    else:
                        results[solver_name] = output
        
        return results

    async def _run_perplexity_solver(self, market_question: str) -> PerplexityResult:
        """Run the Perplexity solver."""
        result = await Runner.run(perplexity_solver, market_question)
        return result.final_output_as(PerplexityResult)

    async def _run_code_runner_solver(
        self, 
        market_question: str, 
        proposal_data: Dict[str, Any]
    ) -> CodeRunnerResult:
        """Run the Code Runner solver."""
        # Enhance the prompt with API context and sample functions
        enhanced_prompt = f"""Market Question:
{market_question}

API Configuration:
{self._format_api_sources_for_code_runner()}

Proposal Context:
- Query ID: {proposal_data.get('query_id', 'unknown')}
- Block time: {proposal_data.get('request_timestamp', 0)}
- Tags: {', '.join(proposal_data.get('tags', []))}
- Resolution conditions: {proposal_data.get('resolution_conditions', '')}

IMPORTANT: Use the sample function templates provided in your instructions as starting points. These have been proven to work with the APIs and handle edge cases properly.

Please generate and execute code to fetch the precise data needed to answer this market question."""
        
        result = await Runner.run(code_runner_solver, enhanced_prompt)
        return result.final_output_as(CodeRunnerResult)

    def _format_api_sources_for_code_runner(self) -> str:
        """Format API sources information for code runner."""
        if not self.api_keys_config.get("data_sources"):
            return "Standard API sources available (Binance, Sports Data IO)"
        
        formatted = "Available API Data Sources:\n"
        for source in self.api_keys_config["data_sources"]:
            formatted += f"- {source['name']} ({source['category']})\n"
            formatted += f"  Description: {source['description']}\n"
            formatted += f"  API Keys: {', '.join(source['api_keys'])}\n"
            if 'endpoints' in source:
                formatted += f"  Primary endpoint: {source['endpoints']['primary']}\n"
            formatted += "\n"
        
        return formatted

    async def _evaluate_results(
        self,
        market_question: str,
        solver_results: Dict[str, Any],
        routing_decision: RoutingDecision,
        proposal_data: Dict[str, Any]
    ) -> OverseerDecision:
        """Evaluate solver results with the overseer."""
        if self.verbose:
            print("👁️  Evaluating results with overseer...")
        
        with custom_span("Overseer evaluation"):
            # Prepare evaluation context
            evaluation_context = f"""Market Question:
{market_question}

Routing Decision:
- Selected solvers: {', '.join(routing_decision.solvers)}
- Routing reason: {routing_decision.reason}
- Multi-solver strategy: {routing_decision.multi_solver_strategy}

Solver Results:
"""
            
            for solver_name, result in solver_results.items():
                evaluation_context += f"\n{solver_name.upper()} SOLVER:"
                if isinstance(result, dict) and "error" in result:
                    evaluation_context += f"\n- Error: {result['error']}"
                    evaluation_context += f"\n- Recommendation: {result.get('recommendation', 'p4')}"
                else:
                    evaluation_context += f"\n- Recommendation: {result.recommendation}"
                    evaluation_context += f"\n- Reasoning: {result.reasoning}"
                    if hasattr(result, 'confidence'):
                        evaluation_context += f"\n- Confidence: {result.confidence}"
                    if hasattr(result, 'sources'):
                        evaluation_context += f"\n- Sources: {', '.join(result.sources[:3])}"  # Limit sources
            
            # Add market pricing context
            proposed_price = proposal_data.get('proposed_price', 0)
            proposed_outcome = proposal_data.get('proposed_price_outcome', '')
            if proposed_outcome:
                evaluation_context += f"\n\nMarket Context:"
                evaluation_context += f"\n- Current proposal: {proposed_outcome} at price {proposed_price}"
                evaluation_context += f"\n- This suggests market sentiment toward {proposed_outcome}"
            
            result = await Runner.run(overseer_agent, evaluation_context)
            return result.final_output_as(OverseerDecision)

    def _compile_final_result_with_journey(
        self,
        proposal_data: Dict[str, Any],
        journey: List[Dict[str, Any]],
        final_recommendation: str,
        start_time: float
    ) -> Dict[str, Any]:
        """Compile the final result with journey tracking."""
        # Generate timestamp for the result
        timestamp = time.time()
        processing_date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        query_id = proposal_data.get('query_id', 'unknown')
        short_id = query_id[:8] if len(query_id) > 8 else query_id
        
        # Build the result structure compatible with existing system
        result = {
            # Core identification
            "query_id": query_id,
            "short_id": short_id,
            "question_id_short": short_id,
            "timestamp": timestamp,
            "format_version": 2,
            
            # Final recommendation (this is what the system uses)
            "recommendation": final_recommendation,
            
            # Resolution info
            "resolved_price": proposal_data.get('resolved_price'),
            "resolved_price_outcome": proposal_data.get('resolved_price_outcome'),
            "proposed_price": proposal_data.get('proposed_price', 0),
            
            # Metadata
            "metadata": {
                "processed_file": f"questionId_{short_id}.json",
                "processing_timestamp": timestamp,
                "processing_date": processing_date
            },
            
            # Proposal metadata (maintain compatibility)
            "proposal_metadata": {
                "query_id": proposal_data.get('query_id'),
                "transaction_hash": proposal_data.get('transaction_hash'),
                "block_number": proposal_data.get('block_number'),
                "request_transaction_block_time": proposal_data.get('request_transaction_block_time'),
                "ancillary_data": proposal_data.get('ancillary_data'),
                "ancillary_data_hex": proposal_data.get('ancillary_data_hex'),
                "resolution_conditions": proposal_data.get('resolution_conditions'),
                "request_timestamp": proposal_data.get('request_timestamp'),
                "expiration_timestamp": proposal_data.get('expiration_timestamp'),
                "creator": proposal_data.get('creator'),
                "proposer": proposal_data.get('proposer'),
                "bond_currency": proposal_data.get('bond_currency'),
                "proposal_bond": proposal_data.get('proposal_bond'),
                "reward_amount": proposal_data.get('reward_amount'),
                "updates": proposal_data.get('updates', []),
                "condition_id": proposal_data.get('condition_id'),
                "tags": proposal_data.get('tags', []),
                "icon": proposal_data.get('icon'),
                "end_date_iso": proposal_data.get('end_date_iso'),
                "game_start_time": proposal_data.get('game_start_time'),
                "tokens": proposal_data.get('tokens', []),
                "neg_risk_market_id": proposal_data.get('neg_risk_market_id', ''),
                "neg_risk_request_id": proposal_data.get('neg_risk_request_id', '')
            },
            
            # Market data section
            "market_data": {
                "disputed": False,
                "recommendation_overridden": False,
                "tags": proposal_data.get('tags', []),
                "end_date_iso": proposal_data.get('end_date_iso'),
                "game_start_time": proposal_data.get('game_start_time'),
                "icon": proposal_data.get('icon'),
                "condition_id": proposal_data.get('condition_id')
            },
            
            # Journey - this is the key tracking feature
            "journey": journey,
            
            # System info for the agentic system
            "system_info": {
                "processing_system": "openai_agentic",
                "processing_timestamp": timestamp,
                "total_processing_time": timestamp - start_time,
                "version": "1.0.0"
            }
        }
        
        return result

    def _compile_final_result(
        self,
        proposal_data: Dict[str, Any],
        routing_decision: RoutingDecision,
        solver_results: Dict[str, Any],
        overseer_decision: OverseerDecision
    ) -> Dict[str, Any]:
        """Compile the final result in the expected format."""
        # Generate timestamp for the result
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_id = proposal_data.get('query_id', 'unknown')
        short_id = query_id[:8] if len(query_id) > 8 else query_id
        
        # Build the result structure compatible with existing system
        result = {
            # Core identification
            "query_id": query_id,
            "short_id": short_id,
            "timestamp": timestamp,
            
            # Final recommendation (this is what the system uses)
            "recommendation": overseer_decision.final_recommendation,
            
            # Proposal metadata (maintain compatibility)
            "proposal_metadata": {
                "query_id": proposal_data.get('query_id'),
                "transaction_hash": proposal_data.get('transaction_hash'),
                "block_number": proposal_data.get('block_number'),
                "request_timestamp": proposal_data.get('request_timestamp'),
                "ancillary_data": proposal_data.get('ancillary_data'),
                "resolution_conditions": proposal_data.get('resolution_conditions'),
                "proposed_price": proposal_data.get('proposed_price'),
                "proposed_price_outcome": proposal_data.get('proposed_price_outcome'),
                "creator": proposal_data.get('creator'),
                "proposer": proposal_data.get('proposer'),
                "tags": proposal_data.get('tags', []),
                "icon": proposal_data.get('icon'),
                "end_date_iso": proposal_data.get('end_date_iso'),
            },
            
            # Top-level fields for compatibility
            "tags": proposal_data.get('tags', []),
            "icon": proposal_data.get('icon'),
            "condition_id": proposal_data.get('condition_id'),
            "ancillary_data": proposal_data.get('ancillary_data'),
            "resolution_conditions": proposal_data.get('resolution_conditions'),
            "proposed_price": proposal_data.get('proposed_price'),
            "proposed_price_outcome": proposal_data.get('proposed_price_outcome'),
            
            # Agentic system specific results
            "agentic_results": {
                "routing_decision": {
                    "solvers": routing_decision.solvers,
                    "reason": routing_decision.reason,
                    "multi_solver_strategy": routing_decision.multi_solver_strategy
                },
                "solver_results": {
                    solver_name: {
                        "recommendation": result.recommendation if hasattr(result, 'recommendation') else result.get('recommendation', 'p4'),
                        "reasoning": result.reasoning if hasattr(result, 'reasoning') else str(result),
                        "confidence": result.confidence if hasattr(result, 'confidence') else "unknown",
                        "additional_data": self._extract_additional_data(result)
                    }
                    for solver_name, result in solver_results.items()
                },
                "overseer_evaluation": {
                    "verdict": overseer_decision.verdict,
                    "require_rerun": overseer_decision.require_rerun,
                    "reason": overseer_decision.reason,
                    "critique": overseer_decision.critique,
                    "market_alignment": overseer_decision.market_alignment,
                    "confidence_score": overseer_decision.confidence_score
                }
            },
            
            # System metadata
            "system_info": {
                "processing_system": "openai_agentic",
                "processing_timestamp": timestamp,
                "agents_used": routing_decision.solvers,
                "total_processing_time": None,  # Could be calculated
                "version": "1.0.0"
            }
        }
        
        return result

    def _extract_additional_data(self, result: Any) -> Dict[str, Any]:
        """Extract additional data from solver results."""
        additional = {}
        
        if hasattr(result, 'sources'):
            additional['sources'] = result.sources
        if hasattr(result, 'code_executed'):
            additional['code_executed'] = result.code_executed
        if hasattr(result, 'data_retrieved'):
            additional['data_retrieved'] = result.data_retrieved
        
        return additional

    async def process_proposals_from_directory(
        self, 
        proposals_dir: str, 
        output_dir: str,
        max_proposals: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple proposals from a directory.
        
        Args:
            proposals_dir: Directory containing proposal JSON files
            output_dir: Directory to save results
            max_proposals: Maximum number of proposals to process (None for all)
            
        Returns:
            List of results
        """
        proposals_path = Path(proposals_dir)
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)
        
        # Find all proposal JSON files
        proposal_files = list(proposals_path.glob("questionId_*.json"))
        
        if max_proposals:
            proposal_files = proposal_files[:max_proposals]
        
        if self.verbose:
            print(f"📁 Found {len(proposal_files)} proposal files to process")
        
        results = []
        
        for i, proposal_file in enumerate(proposal_files):
            if self.verbose:
                print(f"\n📄 Processing {i+1}/{len(proposal_files)}: {proposal_file.name}")
            
            try:
                # Load proposal data
                with open(proposal_file, 'r') as f:
                    proposal_data = json.load(f)
                
                # Handle both single proposal and list format
                if isinstance(proposal_data, list) and len(proposal_data) > 0:
                    proposal_data = proposal_data[0]
                
                # Process the proposal
                result = await self.process_proposal(proposal_data)
                results.append(result)
                
                # Save individual result
                output_file = output_path / f"result_{result['short_id']}_{result['timestamp']}.json"
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)
                
                if self.verbose:
                    print(f"💾 Saved result to {output_file}")
                
            except Exception as e:
                if self.verbose:
                    print(f"❌ Error processing {proposal_file}: {str(e)}")
                continue
        
        if self.verbose:
            print(f"\n🎉 Completed processing {len(results)} proposals")
        
        return results