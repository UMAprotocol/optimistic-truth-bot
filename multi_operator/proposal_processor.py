#!/usr/bin/env python3
"""
UMA Multi-Operator Proposal Processor

This script monitors for new proposals in the specified directory,
routes them to the appropriate solver, and processes them using the
solver and overseer components.
"""

import os
import json
import time
import sys
import argparse
import threading
import traceback
import importlib
import signal
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Import local modules
from .common import (
    setup_logging,
    format_prompt_from_json,
    get_query_id_from_proposal,
    get_question_id_short,
    get_output_filename,
    should_process_proposal,
    get_token_price,
    validate_output_json,
)
from .router.router import Router
from .overseer.overseer import Overseer
from .solvers.perplexity_solver import PerplexitySolver
from .solvers.code_runner import CodeRunnerSolver
from .prompts.overseer_prompt import format_market_price_info


class MultiOperatorProcessor:
    """
    Main processor that monitors for new proposals and processes them using
    the router, solver, and overseer components.
    """

    def __init__(
        self,
        proposals_dir=None,
        output_dir=None,
        max_attempts=3,
        min_attempts=2,
        start_block_number=0,
        poll_interval=30,
        verbose=False,
        api_keys_config=None,
    ):
        """
        Initialize the processor.

        Args:
            proposals_dir: Directory containing proposals
            output_dir: Directory to save output files
            max_attempts: Maximum number of attempts for a proposal
            min_attempts: Minimum number of attempts before defaulting to p4
            start_block_number: Block number to start processing from
            poll_interval: Interval in seconds to poll for new proposals
            verbose: Whether to print verbose output
            api_keys_config: Path to a configuration file containing API keys for code runner
        """
        # Load environment variables
        load_dotenv()
        self.verbose = verbose
        self.api_keys_config = api_keys_config

        # Set up logging
        self.logger = setup_logging(
            "multi_operator_processor", "logs/multi_operator_processor.log"
        )

        # Initialize logging state variables
        self._last_scan_log_hour = datetime.now().hour

        # Verify API keys
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        if not self.perplexity_api_key:
            self.logger.error("PERPLEXITY_API_KEY not found in environment variables")
            sys.exit(1)

        if not self.openai_api_key:
            self.logger.error("OPENAI_API_KEY not found in environment variables")
            sys.exit(1)

        # Set directories
        self.proposals_dir = Path(proposals_dir) if proposals_dir else Path("proposals")
        self.proposals_dir.mkdir(exist_ok=True)

        # Determine if output should be saved
        self.save_output = output_dir is not None
        self.output_dir = None

        # Set up output directory if saving is enabled
        if self.save_output:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(exist_ok=True)
            self.logger.info(f"Output will be saved to: {self.output_dir}")
        else:
            self.logger.info(
                "No output directory specified - results will only be logged (not saved to files)"
            )

        # Store configuration
        self.max_attempts = max_attempts
        self.min_attempts = min_attempts
        self.start_block_number = start_block_number
        self.poll_interval = poll_interval
        
        # Set some important constants
        self.P3_P4_RECOMMENDATIONS = ["p3", "p4"]  # Special recommendations requiring minimum attempts

        # Load solver system prompt
        self.load_solver_prompt()

        # Track processed files to avoid duplicate processing
        self.processed_files = set()

        # Track query_ids that already have existing output files
        self.processed_query_ids = set()

        # If we have an output directory, scan it for existing result files
        if self.save_output and self.output_dir:
            self._load_processed_query_ids()

        # Flag to control running status
        self.running = False

        # Initialize components
        self.initialize_components()

        self.logger.info("Multi-Operator Processor initialized")
        self.logger.info(f"Proposals directory: {self.proposals_dir}")
        self.logger.info(f"Max attempts: {self.max_attempts}")
        self.logger.info(f"Min attempts: {self.min_attempts}")
        self.logger.info(f"Start block number: {self.start_block_number}")
        self.logger.info(f"Poll interval: {self.poll_interval} seconds")
        self.logger.info(f"Verbose: {self.verbose}")

    def _load_processed_query_ids(self):
        """Load all query_ids that already have result files in the output directory."""
        if not self.output_dir:
            return

        # Look for result files matching pattern result_XXXXXXXX_*.json
        result_files = self.output_dir.glob("result_*_*.json")
        query_ids_loaded = 0

        for file_path in result_files:
            try:
                # Extract the short_id from the filename (result_SHORT_ID_TIMESTAMP.json)
                filename = file_path.name
                if filename.startswith("result_") and "_" in filename:
                    parts = filename.split("_")
                    if len(parts) >= 3:
                        short_id = parts[1]
                        self.processed_query_ids.add(short_id)
                        query_ids_loaded += 1
            except Exception as e:
                self.logger.error(
                    f"Error processing existing result file {file_path}: {e}"
                )

        self.logger.info(
            f"Loaded {query_ids_loaded} existing query IDs from output directory"
        )

    def load_solver_prompt(self):
        """Load the solver system prompt from the perplexity_prompt module."""
        try:
            # Import the prompt module from our new location
            from .prompts.perplexity_prompt import get_system_prompt
            self.get_system_prompt = get_system_prompt
            self.logger.info("Successfully loaded system prompt from perplexity_prompt.py")
        except (ImportError, AttributeError) as e:
            self.logger.error(f"Error loading system prompt: {e}")
            self.logger.error("Using default system prompt")

            # Define a fallback system prompt
            def fallback_prompt(version=None):
                return (
                    "You are an artificial intelligence oracle that resolves UMA optimistic oracle requests "
                    "based strictly on verified facts. Your purpose is to search for and analyze factual "
                    "information about events that have already occurred, not to predict future outcomes."
                )

            self.get_system_prompt = fallback_prompt

    def _load_api_keys_and_data_sources(self):
        """Load API keys and data sources from config file.
        
        Returns:
            tuple: (api_keys, data_sources)
        """
        api_keys = []
        data_sources = {}
        
        if not self.api_keys_config:
            return api_keys, data_sources
            
        try:
            with open(self.api_keys_config, 'r') as f:
                config_data = json.load(f)
                
                # Process data sources if available
                if 'data_sources' in config_data:
                    for source in config_data['data_sources']:
                        # Extract all API keys
                        if 'api_keys' in source and isinstance(source['api_keys'], list):
                            api_keys.extend(source['api_keys'])
                        
                        # Store data sources by name
                        if 'name' in source:
                            name = source['name']
                            data_sources[name] = source
            
            # Ensure NHL API key is always available if NHL source exists
            nhl_sources = [name for name in data_sources if 'NHL' in name.upper()]
            if nhl_sources and "SPORTS_DATA_IO_NHL_API_KEY" not in api_keys:
                api_keys.append("SPORTS_DATA_IO_NHL_API_KEY")
                
            self.logger.info(f"Loaded {len(api_keys)} API keys and {len(data_sources)} data sources from config")
                
        except Exception as e:
            self.logger.error(f"Error loading API keys config: {e}")
            
        return api_keys, data_sources

    def initialize_components(self):
        """Initialize the router, solver, and overseer components."""
        self.logger.info("Initializing components")

        # Load API keys and data sources from config
        api_keys, data_sources = self._load_api_keys_and_data_sources()
                
        # Initialize solvers
        self.solvers = {
            "perplexity": PerplexitySolver(
                api_key=self.perplexity_api_key, verbose=self.verbose
            ),
            "code_runner": CodeRunnerSolver(
                api_key=self.openai_api_key,
                verbose=self.verbose,
                config_file=self.api_keys_config,
                additional_api_keys=api_keys,
            ),
        }
        
        # Get consolidated API keys and data sources
        if "code_runner" in self.solvers:
            code_runner = self.solvers["code_runner"]
            # Add keys from code runner if not already present
            if hasattr(code_runner, "available_api_keys"):
                for key in code_runner.available_api_keys:
                    if key not in api_keys:
                        api_keys.append(key)
            # Add data sources from code runner if not already present
            if hasattr(code_runner, "data_sources"):
                for name, source in code_runner.data_sources.items():
                    if name not in data_sources:
                        data_sources[name] = source
            
        # Initialize router with API keys and data sources
        self.router = Router(
            api_key=self.openai_api_key, 
            verbose=self.verbose, 
            available_api_keys=api_keys,
            data_sources=data_sources
        )

        # Initialize overseer
        self.overseer = Overseer(api_key=self.openai_api_key, verbose=self.verbose)
        
        self.logger.info(f"Initialized {len(self.solvers)} solvers with {len(api_keys)} API keys and {len(data_sources)} data sources")

    def scan_proposals(self):
        """Scan for new proposals in the proposals directory."""
        # Only log scanning message if we find new proposals
        new_proposals = []

        # Scan for JSON files in the proposals directory
        for file_path in self.proposals_dir.glob("*.json"):
            file_str = str(file_path)

            # Skip already processed files
            if file_str in self.processed_files:
                continue

            try:
                # Read the proposal file
                with open(file_path, "r") as f:
                    proposal_data = json.load(f)

                # Check if the proposal should be processed based on block number
                if should_process_proposal(proposal_data, self.start_block_number):
                    # Extract query ID for logging
                    query_id = get_query_id_from_proposal(proposal_data)
                    short_id = get_question_id_short(query_id)

                    # Skip if we've already processed this query_id in a previous run
                    if short_id in self.processed_query_ids:
                        self.logger.info(
                            f"Skipping proposal with ID {short_id} - existing output file found"
                        )
                        # Mark as processed
                        self.processed_files.add(file_str)
                        continue

                    self.logger.info(
                        f"Found new proposal: {short_id} ({file_path.name})"
                    )

                    new_proposals.append(
                        {
                            "file_path": file_path,
                            "proposal_data": proposal_data,
                            "query_id": query_id,
                            "short_id": short_id,
                        }
                    )
                else:
                    # Mark as processed but do not process
                    self.processed_files.add(file_str)
            except Exception as e:
                self.logger.error(f"Error reading proposal file {file_path}: {e}")
                # Don't mark as processed so we'll try again next time

        return new_proposals

    def process_proposal(self, proposal_info):
        """
        Process a single proposal using the router, solver, and overseer.

        Args:
            proposal_info: Dictionary containing proposal information

        Returns:
            Dictionary containing the processing results
        """
        file_path = proposal_info["file_path"]
        proposal_data = proposal_info["proposal_data"]
        query_id = proposal_info["query_id"]
        short_id = proposal_info["short_id"]

        self.logger.info(f"Processing proposal: {short_id}")
        if self.verbose:
            print(f"\n{'='*80}")
            print(f"📋 PROCESSING PROPOSAL: \033[1m\033[36m{short_id}\033[0m")
            print(f"📄 File: {file_path}")
            print(f"🆔 Query ID: {query_id}")
            print(f"{'='*80}")

        # Mark the file as processed
        self.processed_files.add(str(file_path))

        try:
            # Extract token information if available
            tokens = None
            market_price_info = None
            is_list = isinstance(proposal_data, list) and len(proposal_data) > 0
            proposal_obj = proposal_data[0] if is_list else proposal_data

            if "tokens" in proposal_obj:
                tokens = proposal_obj["tokens"]
                # Add resolution conditions to tokens to ensure proper market alignment checking
                if "resolution_conditions" in proposal_obj:
                    # Create a copy to avoid modifying the original proposal data
                    if isinstance(tokens, list) and len(tokens) > 0:
                        tokens_copy = tokens.copy()
                        # Add resolution conditions to the first token for reference
                        if isinstance(tokens_copy[0], dict):
                            tokens_copy[0]["resolution_conditions"] = proposal_obj["resolution_conditions"]
                        tokens = tokens_copy
                
                market_price_info = format_market_price_info(tokens)

            # Format the prompt using proposal data
            user_prompt = format_prompt_from_json(proposal_data)
            if not user_prompt:
                self.logger.error(f"Failed to format prompt from proposal: {short_id}")
                return None

            # Get the system prompt
            if not hasattr(self, "get_system_prompt"):
                self.load_solver_prompt()
            system_prompt = self.get_system_prompt()

            # Track all solver results for potential rerouting
            all_solver_results = []
            attempted_solvers = []
            current_routing_attempt = 1
            max_routing_attempts = 2  # Maximum number of times to try re-routing

            # Keep track of excluded solvers and overseer guidance for re-routing
            excluded_solvers = []
            overseer_guidance = None

            while current_routing_attempt <= max_routing_attempts:
                self.logger.info(
                    f"Routing attempt {current_routing_attempt}/{max_routing_attempts}"
                )

                # Router: Decide which solver(s) to use
                route_result = self.router.route(
                    user_prompt=user_prompt,
                    available_solvers=list(self.solvers.keys()),
                    excluded_solvers=excluded_solvers,
                    overseer_guidance=overseer_guidance,
                    model="gpt-4-turbo",
                )

                solvers_to_use = route_result.get("solvers", ["perplexity"])
                route_reason = route_result.get("reason", "Default routing")
                multi_solver_strategy = route_result.get("multi_solver_strategy", "")

                self.logger.info(f"Router selected solvers: {solvers_to_use}")
                self.logger.info(f"Router reason: {route_reason}")
                if multi_solver_strategy:
                    self.logger.info(f"Multi-solver strategy: {multi_solver_strategy}")

                if self.verbose:
                    print(
                        f"\n🔀 ROUTER DECISION (Attempt {current_routing_attempt}/{max_routing_attempts}):"
                    )
                    print(f"Solvers: {solvers_to_use}")
                    print(f"Reason: {route_reason}")
                    if multi_solver_strategy:
                        print(f"Multi-solver strategy: {multi_solver_strategy}")
                    if excluded_solvers:
                        print(f"Excluded solvers: {excluded_solvers}")
                    print(f"{'='*80}\n")

                # Process with each solver, with retry support
                solver_results = []
                for solver_name in solvers_to_use:
                    # Track that we attempted this solver
                    if solver_name not in attempted_solvers:
                        attempted_solvers.append(solver_name)

                    max_attempts = self.max_attempts  # Default max attempts
                    current_attempt = 1
                    updated_system_prompt = system_prompt
                    final_solver_result = None

                    while current_attempt <= max_attempts:
                        self.logger.info(
                            f"Processing with {solver_name}, attempt {current_attempt}/{max_attempts}"
                        )

                        # Get the solver
                        if solver_name not in self.solvers:
                            self.logger.error(f"Solver {solver_name} not found")
                            solver_result = {
                                "error": f"Solver {solver_name} not found",
                                "recommendation": "p4",  # Default to p4
                            }
                            solver_results.append(solver_result)
                            break

                        solver = self.solvers[solver_name]

                        # Process with the solver
                        solver_result = solver.solve(
                            user_prompt=user_prompt, system_prompt=updated_system_prompt
                        )

                        # Keep track of the current result
                        current_solver_result = {
                            "solver": solver_name,
                            "solver_result": solver_result,
                            "recommendation": solver_result.get("recommendation", "p4"),
                            "response": solver_result.get("response", ""),
                            "attempt": current_attempt,
                            "execution_successful": solver_result.get(
                                "response_metadata", {}
                            ).get("execution_successful", True),
                        }

                        # Evaluate with overseer
                        solver_recommendation = solver_result.get(
                            "recommendation", "p4"
                        )
                        solver_response = solver_result.get("response", "")

                        # For code_runner, include the generated code in the response so the overseer can see the logic
                        if solver_name == "code_runner":
                            code = solver_result.get("code", "")
                            code_output = solver_result.get("code_output", "")
                            enhanced_response = f"""CODE RUNNER SOLUTION:

GENERATED CODE:
```python
{code}
```

CODE EXECUTION OUTPUT:
```
{code_output}
```

SUMMARY:
{solver_response}
"""
                            solver_response = enhanced_response

                        overseer_result = self.overseer.evaluate(
                            user_prompt=user_prompt,
                            system_prompt=updated_system_prompt,
                            solver_response=solver_response,
                            recommendation=solver_recommendation,
                            attempt=current_attempt,
                            tokens=tokens,
                            solver_name=solver_name,
                            model="gpt-4-turbo",
                        )

                        # Add overseer result to current result
                        current_solver_result["overseer_result"] = overseer_result

                        # Check if overseer is satisfied or we need to retry
                        overseer_decision = overseer_result["decision"]
                        verdict = overseer_decision.get("verdict", "DEFAULT_TO_P4")
                        require_rerun = overseer_decision.get("require_rerun", False)
                        market_alignment = overseer_decision.get("market_alignment", "")
                        prompt_update = overseer_decision.get("prompt_update", "")

                        self.logger.info(
                            f"Overseer verdict for {solver_name}: {verdict}, require_rerun: {require_rerun}"
                        )

                        if self.verbose:
                            verdict_display = (
                                "✅ SATISFIED"
                                if verdict == "SATISFIED"
                                else (
                                    "🔄 RETRY"
                                    if verdict == "RETRY"
                                    else "⚠️ DEFAULT_TO_P4"
                                )
                            )
                            print(f"Overseer verdict: {verdict_display}")
                            print(
                                f"Reason: {overseer_decision.get('reason', 'No reason provided')}"
                            )
                            if "market_alignment" in overseer_decision:
                                print(
                                    f"Market alignment: {overseer_decision['market_alignment']}"
                                )
                            if require_rerun:
                                print(f"Requires rerun: Yes")
                            print("-" * 40)

                        # Check for market alignment issues that require re-routing
                        market_misalignment = False
                        if ("STRONGLY" in market_alignment and 
                            ("does not align" in market_alignment.lower() or 
                             "not align" in market_alignment.lower() or
                             "contradicts" in market_alignment.lower())):
                            
                            # If we see strong market misalignment, this is a serious issue
                            # We should always consider trying a different solver, even if not explicitly mentioned
                            self.logger.info(
                                f"Strong market misalignment detected with {solver_name} solver - re-routing recommended"
                            )
                            
                            # Store the current result for the re-routing decision later
                            solver_results.append(current_solver_result)
                            all_solver_results.append(current_solver_result)
                            
                            # Set a flag to indicate we need to break from this solver and try a different one
                            market_misalignment = True
                            final_solver_result = current_solver_result
                            
                            # If this is our first attempt, force re-routing to try to honor min_attempts with different solvers
                            if current_attempt == 1 or current_routing_attempt < max_routing_attempts:
                                self.logger.info(f"Early market misalignment detected - will try re-routing to different solver")
                                break
                        
                        # Check if recommendation is p3 or p4 OR if overseer defaulted to p4
                        recommendation = current_solver_result.get("recommendation", "")
                        recommendation_is_special = recommendation.lower() in self.P3_P4_RECOMMENDATIONS
                        overseer_defaulted_to_p4 = verdict.lower() == "default_to_p4"
                        should_enforce_min_attempts = (recommendation_is_special or overseer_defaulted_to_p4) and current_attempt < self.min_attempts
                        
                        if verdict == "SATISFIED" and not should_enforce_min_attempts:
                            # Overseer is satisfied with the result
                            final_solver_result = current_solver_result
                            break
                        elif (
                            (verdict == "RETRY" or should_enforce_min_attempts)
                            and (require_rerun or should_enforce_min_attempts)
                            and current_attempt < max_attempts
                            and not market_misalignment
                        ):
                            # Force another attempt if we got p3/p4 and haven't reached min_attempts
                            if should_enforce_min_attempts:
                                self.logger.info(
                                    f"Recommendation {recommendation} requires minimum {self.min_attempts} attempts, currently at {current_attempt}. Enforcing another attempt."
                                )
                            
                            # Update the system prompt if the overseer provided additional guidance
                            if prompt_update:
                                updated_system_prompt = f"{updated_system_prompt}\n\nADDITIONAL INSTRUCTIONS: {prompt_update}"
                                self.logger.info(
                                    f"Updated system prompt for {solver_name} retry"
                                )
                            elif should_enforce_min_attempts:
                                # Add guidance for p3/p4 cases
                                updated_system_prompt = f"{updated_system_prompt}\n\nADDITIONAL INSTRUCTIONS: Your previous response returned {recommendation}. Please try again with a different approach or by checking alternative data sources. If the issue is with data availability or API access, consider whether the market conditions provided in the prompt could help inform the recommendation."
                                self.logger.info(
                                    f"Added special guidance for {recommendation} retry"
                                )

                            # Store the current result and try again
                            solver_results.append(current_solver_result)
                            all_solver_results.append(current_solver_result)
                            current_attempt += 1
                        else:
                            # Either DEFAULT_TO_P4 or reached max attempts
                            final_solver_result = current_solver_result
                            break

                    # Add the final result if not already added
                    if (
                        final_solver_result
                        and final_solver_result not in solver_results
                    ):
                        solver_results.append(final_solver_result)
                        all_solver_results.append(final_solver_result)

                # If no more routing attempts needed or we have successful results, break the routing loop
                if current_routing_attempt >= max_routing_attempts:
                    break

                # Otherwise, check if we need to re-route based on solver results
                # Ask the overseer for re-routing advice
                reroute_result = self.overseer.suggest_reroute(
                    user_prompt=user_prompt,
                    system_prompt=system_prompt,
                    solver_results=all_solver_results,
                    attempted_solvers=attempted_solvers,
                    all_available_solvers=list(self.solvers.keys()),
                    max_solver_attempts=self.max_attempts,
                    model="gpt-4-turbo",
                )

                # If the overseer suggests re-routing, prepare for next routing attempt
                if reroute_result.get("should_reroute", False):
                    self.logger.info("Overseer suggests re-routing")

                    # Update excluded solvers and overseer guidance
                    excluded_solvers = reroute_result.get("excluded_solvers", [])
                    overseer_guidance = reroute_result.get("routing_guidance", "")
                    
                    # Add specific guidance for p3/p4 cases if needed
                    for solver_result in solver_results:
                        if solver_result.get("recommendation", "").lower() in self.P3_P4_RECOMMENDATIONS:
                            if not overseer_guidance:
                                overseer_guidance = "The previous solver(s) returned p3 or p4 recommendations. Please consider using a different approach or combination of solvers that might have access to the required data."
                            break

                    # Add specific guidance for market misalignment cases
                    if "strong" in overseer_guidance.lower() and "market" in overseer_guidance.lower():
                        if "perplexity" not in overseer_guidance.lower():
                            # If market alignment issues detected but perplexity not specifically mentioned, suggest trying it
                            overseer_guidance += " Consider including the perplexity solver which may have more current information about this event."
                    
                    self.logger.info(
                        f"Re-routing with excluded solvers: {excluded_solvers}"
                    )
                    self.logger.info(f"Overseer guidance: {overseer_guidance}")

                    # Increment routing attempt counter
                    current_routing_attempt += 1
                else:
                    # No re-routing needed, break the loop
                    self.logger.info("Overseer does not suggest re-routing")
                    break

            # If multiple solvers were used, we need to have the overseer evaluate all results
            final_result = None
            if len(solver_results) > 1:
                self.logger.info(f"Processing multiple solver results with overseer")

                # Build a combined solver response for the overseer
                combined_response = self._build_combined_response(solver_results)

                # Determine recommendation from the combined results
                # We'll use the most common recommendation, defaulting to p4 if tied
                recommendations = [
                    r.get("recommendation", "p4") for r in solver_results
                ]
                from collections import Counter

                counter = Counter(recommendations)
                most_common = counter.most_common()

                # Default to p4 if we have a tie for most common
                if len(most_common) > 1 and most_common[0][1] == most_common[1][1]:
                    combined_recommendation = "p4"
                else:
                    combined_recommendation = most_common[0][0]

                # Evaluate with overseer
                overseer_result = self.overseer.evaluate(
                    user_prompt=user_prompt,
                    system_prompt=system_prompt,
                    solver_response=combined_response,
                    recommendation=combined_recommendation,
                    attempt=1,
                    tokens=tokens,
                    solver_name="multiple_solvers",
                    model="gpt-4-turbo",
                )

                # Prepare final result
                overseer_decision = overseer_result["decision"]

                # CRITICAL FIX: For multiple solvers, also ensure we respect satisfied recommendations
                final_recommendation = combined_recommendation
                if overseer_decision.get("verdict") == "DEFAULT_TO_P4":
                    final_recommendation = "p4"
                elif overseer_decision.get("verdict") == "SATISFIED":
                    # If satisfied, use the combined recommendation
                    final_recommendation = combined_recommendation

                final_result = {
                    "query_id": query_id,
                    "short_id": short_id,
                    "user_prompt": user_prompt,
                    "system_prompt": system_prompt,
                    "router_result": route_result,
                    "solver_results": solver_results,
                    "overseer_result": overseer_result,
                    # Use the fixed recommendation logic
                    "recommendation": final_recommendation,
                    "reason": overseer_decision.get(
                        "reason", "Evaluated by overseer from multiple solver results"
                    ),
                    "market_alignment": overseer_decision.get(
                        "market_alignment", "No market alignment information provided"
                    ),
                    "routing_attempts": current_routing_attempt,
                    "attempted_solvers": attempted_solvers,
                    "proposal_metadata": proposal_obj,
                    "file_path": str(file_path),
                    "rerouting_info": (
                        {
                            "excluded_solvers": excluded_solvers,
                            "overseer_guidance": overseer_guidance,
                        }
                        if current_routing_attempt > 1
                        else None
                    ),
                }

                # Add all_solver_results only if it's different from solver_results
                if all_solver_results != solver_results:
                    final_result["all_solver_results"] = all_solver_results
            else:
                # Find the last result where the overseer was satisfied, or fall back to the last result
                solver_result = None
                satisfied_recommendation = None
                
                # First, try to find the last result where overseer was satisfied
                for result in reversed(solver_results):
                    overseer_result = result.get("overseer_result", {})
                    overseer_decision = overseer_result.get("decision", {})
                    verdict = overseer_decision.get("verdict", "").upper()
                    
                    if verdict == "SATISFIED":
                        solver_result = result
                        satisfied_recommendation = result.get("recommendation", "p4")
                        self.logger.info(f"Using last satisfied result from attempt {result.get('attempt', 'unknown')} with recommendation {satisfied_recommendation}")
                        break
                
                # If no satisfied result found, use the last result overall
                if not solver_result and solver_results:
                    solver_result = solver_results[-1]
                    self.logger.info(f"No satisfied result found, using last result from attempt {solver_result.get('attempt', 'unknown')}")
                
                if not solver_result:
                    self.logger.error(f"No solver result for proposal: {short_id}")
                    return None

                # Construct the final result
                overseer_result = solver_result.get("overseer_result", {})
                overseer_decision = overseer_result.get("decision", {})

                # CRITICAL FIX: Always use the satisfied recommendation if we found one
                final_recommendation = satisfied_recommendation if satisfied_recommendation else solver_result.get("recommendation", "p4")
                
                # Only override the satisfied recommendation if the overseer explicitly defaulted to p4
                if overseer_decision.get("verdict") == "DEFAULT_TO_P4":
                    final_recommendation = "p4"
                elif overseer_decision.get("verdict") == "SATISFIED" and satisfied_recommendation:
                    # Ensure we use the satisfied recommendation, not any other logic
                    final_recommendation = satisfied_recommendation

                final_result = {
                    "query_id": query_id,
                    "short_id": short_id,
                    "user_prompt": user_prompt,
                    "system_prompt": system_prompt,
                    "router_result": route_result,
                    "solver_results": solver_results,
                    "overseer_result": overseer_result,
                    # Use the fixed recommendation logic
                    "recommendation": final_recommendation,
                    "reason": overseer_decision.get("reason", "Evaluated by overseer"),
                    "market_alignment": overseer_decision.get(
                        "market_alignment", "No market alignment information provided"
                    ),
                    "routing_attempts": current_routing_attempt,
                    "attempted_solvers": attempted_solvers,
                    "proposal_metadata": proposal_obj,
                    "file_path": str(file_path),
                    "rerouting_info": (
                        {
                            "excluded_solvers": excluded_solvers,
                            "overseer_guidance": overseer_guidance,
                        }
                        if current_routing_attempt > 1
                        else None
                    ),
                }

                # Add all_solver_results only if it contains different information
                if all_solver_results != solver_results:
                    final_result["all_solver_results"] = all_solver_results

            # Save the result
            if self.save_output:
                # Check if this is a retry and determine run number
                is_retry = proposal_info.get("is_retry", False)
                run_number = None
                if is_retry:
                    run_number = self.get_next_run_number(short_id)
                    self.logger.info(f"Retry detected for {short_id}, using run number: {run_number}")
                
                output_path = self.save_result(final_result, run_number)
                if output_path and self.verbose:
                    self.logger.info(f"Result successfully saved to {output_path}")

            return final_result

        except Exception as e:
            # traceback already imported at the top level

            self.logger.error(f"Error processing proposal {short_id}: {e}")
            self.logger.error(traceback.format_exc())
            return None

    def _build_combined_response(self, solver_results):
        """
        Build a combined response from multiple solver results for the overseer.

        Args:
            solver_results: List of solver results

        Returns:
            Combined response string
        """
        combined = "COMBINED RESULTS FROM MULTIPLE SOLVERS\n\n"

        for result in solver_results:
            solver_name = result.get("solver", "unknown")
            recommendation = result.get("recommendation", "unknown")
            response = result.get("response", "No response")
            overseer_result = result.get("overseer_result", {})
            overseer_decision = (
                overseer_result.get("decision", {}) if overseer_result else {}
            )

            combined += f"===== SOLVER: {solver_name.upper()} =====\n"
            combined += f"RECOMMENDATION: {recommendation}\n"

            # Add market alignment if available
            if "market_alignment" in overseer_decision:
                combined += (
                    f"MARKET ALIGNMENT: {overseer_decision['market_alignment']}\n"
                )

            combined += "\n"

            # For code_runner, include the code in the combined response
            if solver_name == "code_runner" and "solver_result" in result:
                code = result["solver_result"].get("code", "")
                code_output = result["solver_result"].get("code_output", "")

                combined += f"GENERATED CODE:\n```python\n{code}\n```\n\n"
                combined += f"CODE OUTPUT:\n```\n{code_output}\n```\n\n"
                combined += f"SUMMARY:\n{response}\n\n"
            else:
                combined += f"RESPONSE:\n{response}\n\n"

            combined += "=" * 40 + "\n\n"

        return combined

    def run(self):
        """Run the processor to continuously monitor and process proposals."""
        self.running = True
        self.shutdown_requested = False

        # Set up signal handling for graceful shutdown
        def signal_handler(sig, frame):
            self.logger.info("Received shutdown signal, stopping...")
            print("\n\033[1m\033[33m⚠️  Shutting down gracefully, please wait...\033[0m")
            self.running = False
            self.shutdown_requested = True
            # Set a shutdown timer to force exit after 5 seconds if clean shutdown fails
            # threading already imported at the top level

            threading.Timer(
                5.0,
                lambda: print("\n\033[1m\033[31m⚠️  Forcing shutdown...\033[0m")
                or os._exit(0),
            ).start()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        self.logger.info("Starting proposal processor loop")
        if self.verbose:
            # Display a startup banner
            print("\n" + "=" * 80)
            print("\033[1m\033[36m")
            print(
                "  _   _ __  __    _    __  __ _   _ _   _____ ___      ___  ___ _____ ____    _ _____ ___  ___ "
            )
            print(
                " | | | |  \/  |  / \  |  \/  | | | | | |_   _|_ _|    / _ \|  _ \_   _/ ___|  / \_   _/ _ \| _ \\"
            )
            print(
                " | | | | |\/| | / _ \ | |\/| | | | | |   | |  | |    | | | | |_) || || |     | | | || | | |   /"
            )
            print(
                " | |_| | |  | |/ ___ \| |  | | |_| | |___| |  | |    | |_| |  __/ | || |___  | | | || |_| | |\ \\"
            )
            print(
                "  \___/|_|  |_/_/   \_\_|  |_|\___/|_____|_| |___|    \___/|_|    |_| \____|  \_\|_| \___/|_| \_\\"
            )
            print("\033[0m")
            print(
                f"  Version: 1.0.0 | Polling Interval: {self.poll_interval}s | Max Attempts: {self.max_attempts}"
            )
            print("=" * 80 + "\n")

            # Create a box around the monitoring message
            box_width = 80
            message = f"📡 Monitoring {self.proposals_dir} for new proposals... [Press Ctrl+C to stop]"
            padding = (box_width - len(message) - 12) // 2
            print("┌" + "─" * (box_width - 2) + "┐")
            print("│" + " " * padding + message + " " * padding + "│")
            print("└" + "─" * (box_width - 2) + "┘\n")

        while self.running:
            try:
                # Scan for new proposals
                new_proposals = self.scan_proposals()

                # Check if shutdown was requested during scanning
                if self.shutdown_requested:
                    break

                # Add timestamp to scan log message only once per hour when no proposals are found
                current_hour = datetime.now().hour
                if not new_proposals and (
                    not hasattr(self, "_last_scan_log_hour")
                    or self._last_scan_log_hour != current_hour
                ):
                    self._last_scan_log_hour = current_hour
                    self.logger.info(
                        f"Scanning for proposals in {self.proposals_dir} - no new proposals found"
                    )

                if new_proposals:
                    # Log that we found proposals during scanning
                    self.logger.info(
                        f"Scanning for proposals in {self.proposals_dir} found {len(new_proposals)} new proposals to process"
                    )
                    if self.verbose:
                        num_proposals = len(new_proposals)
                        proposal_text = (
                            "proposal" if num_proposals == 1 else "proposals"
                        )
                        print(f"\n{'─'*80}")
                        print(
                            f"🔍 Found \033[1m\033[32m{num_proposals}\033[0m new {proposal_text} to process:"
                        )
                        # List the proposals with their short IDs
                        for i, p in enumerate(new_proposals, 1):
                            print(
                                f"  {i}. \033[36m{p['short_id']}\033[0m ({p['file_path'].name})"
                            )
                        print(f"{'─'*80}")

                    # Process each new proposal (but check shutdown status between proposals)
                    for proposal_info in new_proposals:
                        if self.shutdown_requested:
                            break
                        self.process_proposal(proposal_info)

                # Use smaller sleep intervals to check for shutdown more frequently
                for _ in range(int(self.poll_interval / 0.5)):
                    if self.shutdown_requested:
                        break
                    time.sleep(0.5)
            except Exception as e:
                self.logger.error(f"Error in proposal processor loop: {e}")
                if self.shutdown_requested:
                    break
                time.sleep(1)  # Shorter sleep before retrying

        self.logger.info("Proposal processor stopped")
        print("\033[1m\033[32m✅ Shutdown complete\033[0m")

    def get_next_run_number(self, short_id):
        """Determine the next run number for a given short_id by checking existing files."""
        max_run_number = 1
        
        # Scan output directory for existing files with this short_id
        for filename in os.listdir(self.output_dir):
            if filename.startswith(f"result_{short_id}_") and filename.endswith(".json"):
                # Check if this is a retry file (contains _run-N)
                if "_run-" in filename:
                    # Extract run number from filename like result_e5373cc5_20250603_143022_run-2.json
                    run_part = filename.split("_run-")[-1].replace(".json", "")
                    try:
                        run_number = int(run_part)
                        max_run_number = max(max_run_number, run_number)
                    except ValueError:
                        continue
                else:
                    # This is a base file (run 1), so max should be at least 1
                    max_run_number = max(max_run_number, 1)
        
        return max_run_number + 1

    def save_result(self, result, run_number=None):
        """Save the result to a file."""
        try:
            query_id = result.get("query_id", "")
            short_id = result.get("short_id", "")

            # Create the output file name
            timestamp = int(time.time())
            formatted_time = time.strftime("%Y%m%d_%H%M%S", time.localtime(timestamp))
            
            # Add run number suffix if this is a retry (run_number > 1)
            if run_number and run_number > 1:
                output_file = f"result_{short_id}_{formatted_time}_run-{run_number}.json"
            else:
                output_file = f"result_{short_id}_{formatted_time}.json"
            
            output_path = os.path.join(self.output_dir, output_file)

            # Create a simplified, journey-focused result
            clean_result = {}

            # Create a more organized structure with metadata at the top level
            # and everything else in logical groups
            
            # Top level contains essential identification, format info, and key fields
            clean_result["query_id"] = query_id
            clean_result["short_id"] = short_id
            clean_result["question_id_short"] = short_id  # For backward compatibility
            clean_result["run_iteration"] = run_number if run_number else 1  # Track which run this is
            clean_result["timestamp"] = time.time()
            clean_result["format_version"] = 2  # Indicate this is the new journey-focused format
            
            # Add key fields at the top level for direct access - these should be the primary
            # source of these values, not duplicated in proposal_metadata or market_data
            
            # First, explicitly check if price fields are directly in the result
            top_level_price_fields = ["resolved_price", "resolved_price_outcome", "proposed_price"]
            for key in top_level_price_fields:
                # If the field exists directly in the result, use that
                if key in result:
                    clean_result[key] = result[key]
                # Otherwise check proposal_metadata
                elif "proposal_metadata" in result and result["proposal_metadata"] and key in result["proposal_metadata"]:
                    clean_result[key] = result["proposal_metadata"][key]
            
            # Add the processed file name to metadata
            if "file_path" in result:
                processed_file = os.path.basename(result["file_path"])
            else:
                processed_file = ""
                
            # Create a metadata section for essential information
            clean_result["metadata"] = {
                "processed_file": processed_file,
                "processing_timestamp": time.time(),
                "processing_date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }

            # Proposal metadata goes into its own section
            if "proposal_metadata" in result and result["proposal_metadata"]:
                clean_result["proposal_metadata"] = result["proposal_metadata"].copy()
            else:
                clean_result["proposal_metadata"] = {}

            # List of metadata fields we should ensure are in proposal_metadata
            metadata_fields = [
                "query_id",
                "transaction_hash",
                "block_number",
                "request_transaction_block_time",
                "ancillary_data",
                "ancillary_data_hex",
                "resolution_conditions",
                "proposed_price",
                "proposed_price_outcome",
                "resolved_price",
                "resolved_price_outcome",
                "request_timestamp",
                "expiration_timestamp",
                "creator",
                "proposer",
                "bond_currency",
                "proposal_bond",
                "reward_amount",
                "updates",
                "tags",
                "end_date_iso",
                "game_start_time",
                "tokens",
                "neg_risk_market_id",
                "neg_risk_request_id",
                "icon",
                "condition_id",
            ]
            
            # Initialize market_data object (for backward compatibility)
            clean_result["market_data"] = {}
            
            # Define fields that should only be at the top level, not in proposal_metadata
            top_level_only_fields = ["resolved_price", "resolved_price_outcome", "proposed_price", "proposed_price_outcome"]
            
            # Copy all metadata fields to proposal_metadata except top-level-only fields
            for field in metadata_fields:
                # Skip fields that should be only at the top level
                if field in top_level_only_fields:
                    # Explicitly remove these from proposal_metadata if they somehow got in there
                    if field in clean_result["proposal_metadata"]:
                        del clean_result["proposal_metadata"][field]
                    continue
                    
                # First check if it's in the result directly
                if field in result:
                    clean_result["proposal_metadata"][field] = result[field]
                # Then check if it's not already in proposal_metadata (default values)
                elif field not in clean_result["proposal_metadata"]:
                    # Set default values
                    if field == "tags":
                        clean_result["proposal_metadata"][field] = []
                    elif field == "tokens":
                        clean_result["proposal_metadata"][field] = []
                    elif field == "updates":
                        clean_result["proposal_metadata"][field] = []
                    elif field == "game_start_time":
                        clean_result["proposal_metadata"][field] = None
                    else:
                        clean_result["proposal_metadata"][field] = ""
            
            # Create minimal market_data with ONLY fields that belong exclusively in market_data
            # These fields should NEVER exist at the top level or in proposal_metadata
            clean_result["market_data"] = {
                "disputed": False,
                "recommendation_overridden": False,
                # Include tags and other marker-specific data if available
                "tags": result.get("proposal_metadata", {}).get("tags", []),
                "end_date_iso": result.get("proposal_metadata", {}).get("end_date_iso", ""),
                "game_start_time": result.get("proposal_metadata", {}).get("game_start_time", None),
                "icon": result.get("proposal_metadata", {}).get("icon", ""),
                "condition_id": result.get("proposal_metadata", {}).get("condition_id", "")
            }
            
            # IMPORTANT: Explicitly ensure NO price-related fields in market_data
            price_fields = ["resolved_price", "resolved_price_outcome", "proposed_price", "proposed_price_outcome"]
            for field in price_fields:
                if field in clean_result["market_data"]:
                    del clean_result["market_data"][field]

            # Create the journey array - this is the main change
            journey = []
            
            # Track step number and attempt counters
            step_counter = 1
            attempt_counters = {
                "router": {},  # Key: routing_attempt
                "solver": {},  # Key: solver_name
                "overseer": {}  # Key: solver_evaluated
            }
            
            # Get routing information
            routing_attempts = result.get("routing_attempts", 1)
            
            # Get all solver results, including failed/rejected ones
            all_results = result.get("all_solver_results", [])
            if not all_results and "solver_results" in result:
                all_results = result["solver_results"]  # Fall back to solver_results if all_solver_results is missing
                
            # Add a debug log to trace the inclusion of all steps
            self.logger.info(f"Building journey with {len(all_results)} total solver results (including failed/rejected attempts)")
            
            # For each routing attempt, create journey entries
            for routing_attempt in range(1, routing_attempts + 1):
                # 1. Add router entry for this phase
                if "router_result" in result:
                    router_result = result["router_result"]
                    
                    # Initialize router attempt counter for this phase
                    if routing_attempt not in attempt_counters["router"]:
                        attempt_counters["router"][routing_attempt] = 1
                    
                    # Get router prompt if available
                    router_prompt = None
                    if "prompt" in router_result:
                        router_prompt = router_result["prompt"]
                    elif "router_prompt" in result:
                        router_prompt = result["router_prompt"]
                    
                    # Create comprehensive router entry with flattened structure (no raw_data nesting)
                    router_entry = {
                        "step": step_counter,
                        "actor": "router",
                        "action": "route",
                        "attempt": attempt_counters["router"][routing_attempt],
                        "routing_phase": routing_attempt,
                        "prompt": router_prompt,
                        "response": {
                            "solvers": router_result.get("solvers", []),
                            "reason": router_result.get("reason", ""),
                            "multi_solver_strategy": router_result.get("multi_solver_strategy", "")
                        },
                        # Add detailed timing information
                        "timestamp": time.time(),
                        "start_time": router_result.get("start_time", router_result.get("request_timestamp", time.time() - 2)),  # Try to get original start time
                        "end_time": router_result.get("end_time", time.time()),  # When the routing completed
                        "duration_seconds": router_result.get("duration_seconds", router_result.get("execution_time", 2)),  # How long it took
                        "metadata": {  # Only include truly supplementary metadata, not duplicated data
                            "available_solvers": list(self.solvers.keys()) if hasattr(self, "solvers") else [],
                            "excluded_solvers": result.get("rerouting_info", {}).get("excluded_solvers", []) if routing_attempt > 1 else []
                        }
                    }
                    
                    # Add router response if available but not already included
                    if "response" in router_result and not isinstance(router_result["response"], dict):
                        router_entry["full_response"] = router_result["response"]
                    
                    journey.append(router_entry)
                    step_counter += 1
                
                # 2. Group ALL solver results by routing phase (including failed/rejected attempts)
                solver_results_by_phase = {}
                
                # Process all solver results, not just the ones in solver_results
                for solver_result in all_results:
                    # Try to determine which routing phase this belongs to
                    routing_phase = solver_result.get("routing_phase", 1)  # Default to phase 1 if not specified
                    if "solver_metadata" in solver_result:
                        routing_phase = solver_result["solver_metadata"].get("routing_attempt", routing_phase)
                    
                    if routing_phase not in solver_results_by_phase:
                        solver_results_by_phase[routing_phase] = []
                    
                    solver_results_by_phase[routing_phase].append(solver_result)
                
                # If we still don't have solver results for this phase and we're looking at phase 1,
                # fall back to the original solver_results
                if routing_attempt not in solver_results_by_phase and routing_attempt == 1 and "solver_results" in result:
                    solver_results_by_phase[1] = result["solver_results"]
                
                # 3. Process solver results for this routing phase
                phase_results = solver_results_by_phase.get(routing_attempt, [])
                
                for solver_result in phase_results:
                    solver_name = solver_result.get("solver", "unknown")
                    
                    # Initialize attempt counter for this solver
                    if solver_name not in attempt_counters["solver"]:
                        attempt_counters["solver"][solver_name] = 1
                    
                    # Get current attempt for this solver
                    solver_attempt = attempt_counters["solver"][solver_name]
                    
                    # Get solver prompt with comprehensive extraction, especially for code_runner
                    solver_prompt = None
                    if solver_name == "code_runner":
                        # Try multiple locations where the code runner prompt might be stored
                        if "solver_result" in solver_result:
                            if "code_generation_prompt" in solver_result["solver_result"]:
                                solver_prompt = solver_result["solver_result"]["code_generation_prompt"]
                            elif "full_prompt" in solver_result["solver_result"]:
                                solver_prompt = solver_result["solver_result"]["full_prompt"]
                            elif "prompt" in solver_result["solver_result"]:
                                solver_prompt = solver_result["solver_result"]["prompt"]
                        
                        # Try direct fields in the result object
                        if not solver_prompt:
                            if "code_runner_prompt" in result:
                                solver_prompt = result["code_runner_prompt"] 
                            elif "code_generation_prompt" in result:
                                solver_prompt = result["code_generation_prompt"]
                            elif f"solver_{solver_name}_prompt" in result:
                                solver_prompt = result[f"solver_{solver_name}_prompt"]
                    elif "prompt" in solver_result:
                        # For other solvers, check for a direct prompt field
                        solver_prompt = solver_result["prompt"]
                            
                    # Create solver entry with flattened structure (no raw_data nesting)
                    solver_entry = {
                        "step": step_counter,
                        "actor": solver_name,
                        "action": "solve",
                        "attempt": solver_attempt,
                        "routing_phase": routing_attempt,
                        "prompt": solver_prompt,
                        "response": solver_result.get("response", ""),
                        "recommendation": solver_result.get("recommendation", ""),
                        # Add detailed timing information
                        "timestamp": time.time(),
                        "start_time": solver_result.get("start_time", 
                                      solver_result.get("request_timestamp", 
                                      solver_result.get("solver_result", {}).get("request_timestamp", time.time() - 5))),  # Try to get original start time
                        "end_time": solver_result.get("end_time", 
                                    solver_result.get("solver_result", {}).get("completion_timestamp", time.time())),  # When the solving completed
                        "duration_seconds": solver_result.get("duration_seconds", 
                                           solver_result.get("execution_time", 
                                           solver_result.get("solver_result", {}).get("execution_time", 5))),  # How long it took
                        "status": "success" if solver_result.get("execution_successful", True) else "failure",
                        "metadata": {  # Only include truly supplementary metadata
                            "solver_name": solver_name,
                            "execution_successful": solver_result.get("execution_successful", True),
                            "error": solver_result.get("error", None),  # Include error info if present
                            "failure_reason": solver_result.get("failure_reason", None)
                        }
                    }
                    
                    # Add any execution-specific data directly at the top level rather than nested
                    # Extract useful data from solver_result without duplicating it
                    if "solver_result" in solver_result:
                        solver_result_data = solver_result.get("solver_result", {})
                        
                        # For code_runner, add execution stats and code metrics directly
                        if solver_name == "code_runner":
                            code = solver_result_data.get("code", "")
                            code_output = solver_result_data.get("code_output", "")
                            
                            # Add code metrics
                            if code:
                                solver_entry["code"] = code
                                solver_entry["code_size_bytes"] = len(code)
                                solver_entry["code_line_count"] = len(code.split("\n"))
                                
                            if code_output:
                                solver_entry["code_output"] = code_output
                                solver_entry["code_output_size_bytes"] = len(code_output)
                            
                            # Add API stats if available
                            if "api_stats" in solver_result_data:
                                solver_entry["api_stats"] = solver_result_data["api_stats"]
                                
                            # Add execution environment info if available
                            if "execution_environment" in solver_result_data:
                                solver_entry["execution_environment"] = solver_result_data["execution_environment"]
                    
                    # Add market_misalignment field if present
                    if "market_misalignment" in solver_result and solver_result["market_misalignment"]:
                        solver_entry["market_misalignment"] = True
                    
                    # Add code runner specific data
                    if solver_name == "code_runner" and "solver_result" in solver_result:
                        code = solver_result["solver_result"].get("code", "")
                        code_output = solver_result["solver_result"].get("code_output", "")
                        
                        if code:
                            solver_entry["code"] = code
                        if code_output:
                            solver_entry["code_output"] = code_output
                    
                    journey.append(solver_entry)
                    step_counter += 1
                    
                    # Add overseer evaluation for this solver result
                    if "overseer_result" in solver_result:
                        overseer_result = solver_result["overseer_result"]
                        
                        # Initialize overseer attempt counter
                        if solver_name not in attempt_counters["overseer"]:
                            attempt_counters["overseer"][solver_name] = 1
                        
                        # Get current overseer attempt for this solver
                        overseer_attempt = attempt_counters["overseer"][solver_name]
                        
                        # Get overseer prompt
                        overseer_prompt = None
                        if "prompt" in overseer_result:
                            overseer_prompt = overseer_result["prompt"]
                        elif f"solver_{len(journey)}_overseer_prompt" in result:
                            overseer_prompt = result[f"solver_{len(journey)}_overseer_prompt"]
                        
                        # Get overseer decision
                        overseer_decision = overseer_result.get("decision", {})
                        verdict = overseer_decision.get("verdict", "").lower()
                        require_rerun = overseer_decision.get("require_rerun", False)
                        
                        # Create overseer entry with flattened structure (no raw_data nesting)
                        overseer_entry = {
                            "step": step_counter,
                            "actor": "overseer",
                            "action": "evaluate",
                            "attempt": overseer_attempt,
                            "routing_phase": routing_attempt,
                            "solver_evaluated": solver_name,
                            "prompt": overseer_prompt,
                            "response": overseer_result.get("response", ""),
                            "verdict": verdict,
                            "critique": overseer_decision.get("critique", ""),
                            "market_alignment": overseer_decision.get("market_alignment", ""),
                            "prompt_updated": bool(overseer_decision.get("prompt_update", "")),
                            "prompt_update": overseer_decision.get("prompt_update", ""),  # Include the actual update
                            "require_rerun": require_rerun,
                            "reason": overseer_decision.get("reason", ""),  # Move from metadata to top level
                            # Add detailed timing information
                            "timestamp": time.time(),
                            "start_time": overseer_result.get("start_time", 
                                         overseer_result.get("request_timestamp", time.time() - 3)),  # Try to get original start time
                            "end_time": overseer_result.get("end_time", 
                                       overseer_result.get("completion_timestamp", time.time())),  # When the evaluation completed
                            "duration_seconds": overseer_result.get("duration_seconds", 
                                              overseer_result.get("execution_time", 3)),  # How long it took
                            "status": "rejected" if verdict.lower() in ["retry", "default_to_p4"] else "accepted",
                            "metadata": {  # Only include truly supplementary metadata
                                "evaluated_step": step_counter - 1,  # Reference to the step being evaluated
                                "evaluated_actor": solver_name
                            }
                        }
                        
                        # Add market misalignment flags if applicable
                        if ("STRONGLY" in overseer_decision.get("market_alignment", "") and 
                            ("does not align" in overseer_decision.get("market_alignment", "").lower() or 
                             "not align" in overseer_decision.get("market_alignment", "").lower() or
                             "contradicts" in overseer_decision.get("market_alignment", "").lower())):
                            overseer_entry["market_misalignment"] = True
                        
                        # Add system prompt information if provided
                        if "system_prompt" in result and overseer_entry["prompt_updated"]:
                            prompt_update = overseer_decision.get("prompt_update", "")
                            overseer_entry["system_prompt_before"] = result["system_prompt"]
                            overseer_entry["system_prompt_after"] = f"{result['system_prompt']}\n\nADDITIONAL INSTRUCTIONS: {prompt_update}"
                            overseer_entry["prompt_update"] = prompt_update  # Store explicit prompt update
                        
                        journey.append(overseer_entry)
                        step_counter += 1
                        
                        # If overseer requires a retry, increment solver attempt counter
                        if require_rerun or verdict.lower() == "retry":
                            attempt_counters["solver"][solver_name] += 1
                        
                        # Always increment overseer attempt counter
                        attempt_counters["overseer"][solver_name] += 1
                
                # 4. Add rerouting entry if applicable
                if routing_attempt < routing_attempts and "rerouting_info" in result:
                    rerouting_info = result["rerouting_info"]
                    
                    # Get the latest timing information from the phase to help with timestamps
                    phase_entries = [e for e in journey if e["routing_phase"] == routing_attempt]
                    phase_start_time = min([e.get("start_time", time.time() - 30) for e in phase_entries], default=time.time() - 30) if phase_entries else time.time() - 30
                    phase_end_time = time.time()
                    
                    # Create rerouting entry with flattened structure (no raw_data nesting)
                    rerouting_entry = {
                        "step": step_counter,
                        "actor": "overseer",
                        "action": "reroute",
                        "attempt": 1,  # Rerouting is a new action
                        "routing_phase": routing_attempt,
                        "excluded_solvers": rerouting_info.get("excluded_solvers", []),
                        "routing_guidance": rerouting_info.get("overseer_guidance", ""),
                        # Add detailed timing information
                        "timestamp": time.time(),
                        "start_time": rerouting_info.get("start_time", 
                                     rerouting_info.get("request_timestamp", 
                                     phase_end_time - 2)),  # When the rerouting decision started
                        "end_time": rerouting_info.get("end_time", time.time()),  # When the rerouting completed
                        "duration_seconds": rerouting_info.get("duration_seconds", 2),  # How long it took for the rerouting decision
                        "phase_duration_seconds": phase_end_time - phase_start_time,  # Total duration of the phase being rerouted
                        "reason": rerouting_info.get("reason", "Based on previous solver performance"),
                        # Add phase analysis directly at top level rather than nested
                        "previous_phase_summary": {
                            "attempted_solvers": [entry["actor"] for entry in journey if entry["action"] == "solve" and entry["routing_phase"] == routing_attempt],
                            "phase_verdict": [entry["verdict"] for entry in journey if entry["action"] == "evaluate" and entry["routing_phase"] == routing_attempt],
                            "recommendations": [entry["recommendation"] for entry in journey if entry["action"] == "solve" and entry["routing_phase"] == routing_attempt],
                            "failures": [entry["actor"] for entry in journey if entry["action"] == "solve" and 
                                        entry["routing_phase"] == routing_attempt and 
                                        entry.get("status", "") == "failure"] 
                        },
                        "market_misalignments": [
                            entry["actor"] for entry in journey 
                            if (entry["action"] == "solve" or entry["action"] == "evaluate") and 
                            entry["routing_phase"] == routing_attempt and 
                            entry.get("market_misalignment", False)
                        ],
                        "next_phase": routing_attempt + 1,
                        "metadata": {  # Minimal metadata with only supplementary info
                            "current_phase_start_step": min([e["step"] for e in journey if e["routing_phase"] == routing_attempt], default=step_counter),
                            "current_phase_end_step": step_counter,
                            "phase_start_time": phase_start_time,
                            "phase_end_time": phase_end_time
                        }
                    }
                    
                    journey.append(rerouting_entry)
                    step_counter += 1
                    
                    # Initialize next routing phase
                    attempt_counters["router"][routing_attempt + 1] = 1
            
            # Calculate overall journey timing statistics
            journey_start_time = min([e.get("start_time", e.get("timestamp", time.time())) for e in journey], default=time.time() - 30) if journey else time.time() - 30
            journey_end_time = max([e.get("end_time", e.get("timestamp", time.time())) for e in journey], default=time.time()) if journey else time.time()
            journey_total_duration = journey_end_time - journey_start_time
            
            # Add timing metadata about the journey
            journey_summary = {
                "steps": len(journey),
                "start_time": journey_start_time,
                "end_time": journey_end_time,
                "total_duration_seconds": journey_total_duration,
                "routing_phases": max([e.get("routing_phase", 1) for e in journey], default=1) if journey else 1,
                "step_count_by_actor": {},
                "total_duration_by_actor": {}
            }
            
            # Calculate statistics by actor type
            for entry in journey:
                actor = entry.get("actor", "unknown")
                
                # Count steps by actor
                if actor not in journey_summary["step_count_by_actor"]:
                    journey_summary["step_count_by_actor"][actor] = 0
                journey_summary["step_count_by_actor"][actor] += 1
                
                # Sum duration by actor
                if "duration_seconds" in entry:
                    if actor not in journey_summary["total_duration_by_actor"]:
                        journey_summary["total_duration_by_actor"][actor] = 0
                    journey_summary["total_duration_by_actor"][actor] += entry["duration_seconds"]
            
            # Store the journey as a top-level element
            clean_result["journey"] = journey
            clean_result["journey_summary"] = journey_summary
            
            # Prompts are now included in metadata section
            
            # Create a result section for final outcome and recommendation
            recommendation = result.get("recommendation", "p4")
            
            # Make sure it's a valid recommendation format
            if not recommendation.startswith("p"):
                recommendation = "p4"
            
            clean_result["result"] = {
                "recommendation": recommendation,
                "reason": result.get("reason", ""),
                "market_alignment": result.get("market_alignment", ""),
                "attempted_solvers": result.get("attempted_solvers", []),
                "routing_attempts": result.get("routing_attempts", 1)
            }
            
            # Set recommendation in proposed_price_outcome only at the top level
            # We want to avoid duplicating fields between sections
            clean_result["proposed_price_outcome"] = recommendation
            
            # Ensure price-related fields only exist at the top level
            # Make sure we don't have any price fields in market_data (double-check)
            for field in ["proposed_price", "resolved_price", "proposed_price_outcome", "resolved_price_outcome", "recommendation"]:
                if field in clean_result["market_data"]:
                    del clean_result["market_data"][field]
            
            # Create backward compatibility fields
            # 1. Create old-style recommendation_journey for UI compatibility
            backward_compatible_journey = []
            
            # Track solver-overseer pairs
            solver_overseer_pairs = []
            
            for i in range(0, len(journey)-1):
                if journey[i]["actor"] in ["perplexity", "code_runner"] and journey[i]["action"] == "solve":
                    if i+1 < len(journey) and journey[i+1]["actor"] == "overseer" and journey[i+1]["action"] == "evaluate":
                        solver_overseer_pairs.append((journey[i], journey[i+1]))
            
            # Create backward compatible entries
            for attempt_num, (solver_entry, overseer_entry) in enumerate(solver_overseer_pairs, 1):
                solver_type = solver_entry["actor"]
                
                compatible_entry = {
                    "attempt": attempt_num,
                    "overseer_satisfaction_level": overseer_entry.get("verdict", ""),
                    "prompt_updated": overseer_entry.get("prompt_updated", False),
                    "critique": overseer_entry.get("critique", ""),
                    "routing_attempt": overseer_entry.get("routing_phase", 1)
                }
                
                # Add solver-specific recommendation - only add the field for the actual solver used
                if solver_type == "perplexity":
                    compatible_entry["perplexity_recommendation"] = solver_entry.get("recommendation", "")
                elif solver_type == "code_runner":
                    compatible_entry["code_runner_recommendation"] = solver_entry.get("recommendation", "")
                # No fallback - only add the field for the solver that was actually used
                
                # Add system prompt if available
                if "system_prompt_before" in overseer_entry:
                    compatible_entry["system_prompt_before"] = overseer_entry["system_prompt_before"]
                if "system_prompt_after" in overseer_entry:
                    compatible_entry["system_prompt_after"] = overseer_entry["system_prompt_after"]
                
                backward_compatible_journey.append(compatible_entry)
            
            # Create a minimal overseer_data with just essential information for backward compatibility
            # But no duplicated journey information
            overseer_data = {
                "attempts": len(solver_overseer_pairs),
                "market_price_info": result.get("market_alignment", "No market price information available"),
                "tokens": result.get("tokens", []),
                "recommendation_journey": backward_compatible_journey,
                "journey_ref": True  # Indicate journey is now in top-level key
            }
            
            clean_result["overseer_data"] = overseer_data
            
            # Save the result
            with open(output_path, "w") as f:
                json.dump(clean_result, f, indent=2)

            # Add this short_id to our processed query IDs
            if short_id:
                self.processed_query_ids.add(short_id)

            self.logger.info(f"Result saved to {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"Error saving result: {e}")
            # traceback already imported at the top level
            self.logger.error(traceback.format_exc())
            return None


def main():
    """
    Main entry point for the Multi-Operator Proposal Processor.
    Parses command line arguments and starts the processor.
    """
    parser = argparse.ArgumentParser(
        description="UMA Multi-Operator Proposal Processor"
    )
    parser.add_argument(
        "--proposals-dir",
        type=str,
        help="Directory containing proposal JSON files",
        default="proposals",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Directory to store output files",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=4,
        help="Maximum number of attempts to process a proposal",
    )
    parser.add_argument(
        "--min-attempts",
        type=int,
        default=3,
        help="Minimum number of attempts before defaulting to p4",
    )
    parser.add_argument(
        "--start-block",
        type=int,
        default=0,
        help="Block number to start processing from",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=30,
        help="Interval in seconds to poll for new proposals",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output with detailed logs",
    )
    parser.add_argument(
        "--api-keys-config",
        type=str,
        help="Path to a configuration file containing API keys for code runner",
    )

    args = parser.parse_args()

    print(f"🤖 UMA Multi-Operator Proposal Processor 🤖")
    print(f"Monitoring directory: {args.proposals_dir}")
    if args.api_keys_config:
        print(f"Using API keys config: {args.api_keys_config}")

    processor = MultiOperatorProcessor(
        proposals_dir=args.proposals_dir,
        output_dir=args.output_dir,
        max_attempts=args.max_attempts,
        min_attempts=args.min_attempts,
        start_block_number=args.start_block,
        poll_interval=args.poll_interval,
        verbose=args.verbose,
        api_keys_config=args.api_keys_config,
    )

    processor.run()


if __name__ == "__main__":
    main()
