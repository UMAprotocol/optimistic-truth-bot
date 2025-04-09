#!/usr/bin/env python3
"""
Overseer implementation for UMA Multi-Operator System.
Provides validation and feedback on solver responses.
"""

import logging
import json
import re
from typing import Dict, Any, Optional, Tuple, List

from ..common import query_chatgpt
from .prompt_overseer import get_overseer_prompt, format_market_price_info


class Overseer:
    """
    ChatGPT Overseer for UMA Multi-Operator System.
    Evaluates solver responses for accuracy and completeness.
    """

    def __init__(self, api_key: str, verbose: bool = False):
        """
        Initialize the ChatGPT overseer.

        Args:
            api_key: OpenAI API key
            verbose: Whether to print verbose output
        """
        self.api_key = api_key
        self.verbose = verbose
        self.logger = logging.getLogger("chatgpt_overseer")

    def evaluate(
        self,
        user_prompt: str,
        system_prompt: str,
        solver_response: str,
        recommendation: str,
        attempt: int = 1,
        tokens: Optional[list] = None,
        solver_name: str = "perplexity",
        model: str = "gpt-4-turbo",
    ) -> Dict[str, Any]:
        """
        Evaluate a solver response using the ChatGPT overseer.

        Args:
            user_prompt: The original user prompt
            system_prompt: The system prompt used for the solver
            solver_response: The response from the solver
            recommendation: The recommendation extracted from the solver (p1, p2, p3, p4)
            attempt: The current attempt number
            tokens: Optional list of token objects with price information
            solver_name: The name of the solver that produced the response
            model: The ChatGPT model to use for evaluation

        Returns:
            Dictionary containing the overseer's decision
        """
        self.logger.info(
            f"Evaluating {solver_name} response with ChatGPT overseer (attempt {attempt})"
        )
        if self.verbose:
            print(
                f"Evaluating {solver_name} response with ChatGPT overseer (attempt {attempt})..."
            )

        # Format market price information if tokens are provided
        market_price_info = None
        if tokens:
            market_price_info = format_market_price_info(tokens)
            if self.verbose:
                print("Market price information included in evaluation")

        # Generate the overseer prompt
        overseer_prompt = get_overseer_prompt(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            solver_response=solver_response,
            recommendation=recommendation,
            attempt=attempt,
            market_price_info=market_price_info,
            solver_name=solver_name,
        )

        # Query ChatGPT API
        raw_response = query_chatgpt(
            prompt=overseer_prompt,
            api_key=self.api_key,
            model=model,
            verbose=self.verbose,
        )

        # Extract response text
        response_text = raw_response.choices[0].message.content

        # Get the overseer's decision
        decision = self.extract_decision(response_text)

        if self.verbose:
            print(f"Overseer verdict: {decision.get('verdict', 'Unknown')}")
            print(f"Require rerun: {decision.get('require_rerun', False)}")
            print("-" * 40)
            print("Reason:")
            print(decision.get("reason", "No reason provided"))
            print("-" * 40)

        self.logger.info(f"Overseer verdict: {decision.get('verdict', 'Unknown')}")
        self.logger.info(f"Require rerun: {decision.get('require_rerun', False)}")

        return {"decision": decision, "response": response_text}

    def extract_decision(self, response_text: str) -> Dict[str, Any]:
        """
        Extract the decision from the overseer's response text.

        Args:
            response_text: The response text from the overseer

        Returns:
            Dictionary containing the decision
        """
        # Look for a decision block in the format:
        # ```decision
        # {
        #   "verdict": "SATISFIED",
        #   "require_rerun": false,
        #   "reason": "The response is accurate and can be used confidently.",
        #   "critique": "The response is well-reasoned and addresses all aspects of the query.",
        #   "market_alignment": "The recommendation aligns with market sentiment.",
        #   "prompt_update": ""
        # }
        # ```
        decision_pattern = r"```decision\s*(\{[\s\S]*?\})\s*```"
        match = re.search(decision_pattern, response_text)

        if match:
            try:
                decision = json.loads(match.group(1))
                return decision
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing decision JSON: {e}")
                return self.extract_decision_fallback(response_text)

        return self.extract_decision_fallback(response_text)

    def extract_decision_fallback(self, response_text: str) -> Dict[str, Any]:
        """
        Fallback method to extract decision information from the overseer's response
        if the JSON format is not found or invalid.

        Args:
            response_text: The response text from the overseer

        Returns:
            Dictionary containing the extracted decision
        """
        # Look for verdict patterns
        verdict_pattern = r"(?:verdict|decision):\s*(SATISFIED|RETRY|DEFAULT_TO_P4)"
        verdict_match = re.search(verdict_pattern, response_text, re.IGNORECASE)

        # Look for require_rerun patterns
        rerun_pattern = r"(?:require_rerun|rerun|retry):\s*(true|false)"
        rerun_match = re.search(rerun_pattern, response_text, re.IGNORECASE)

        # Look for reason patterns
        reason_pattern = r"(?:reason|explanation):\s*([^\n]+)"
        reason_match = re.search(reason_pattern, response_text, re.IGNORECASE)

        # Look for critique patterns
        critique_pattern = r"(?:critique|feedback):\s*([^\n]+)"
        critique_match = re.search(critique_pattern, response_text, re.IGNORECASE)

        # Look for market alignment patterns
        market_alignment_pattern = (
            r"(?:market_alignment|market alignment|market|alignment):\s*([^\n]+)"
        )
        market_alignment_match = re.search(
            market_alignment_pattern, response_text, re.IGNORECASE
        )

        # Look for prompt update patterns
        update_pattern = r"(?:prompt_update|update):\s*([^\n]+(?:\n[^\n]+)*)"
        update_match = re.search(update_pattern, response_text, re.IGNORECASE)

        # Construct decision
        decision = {
            "verdict": (
                verdict_match.group(1).upper() if verdict_match else "DEFAULT_TO_P4"
            ),
            "require_rerun": (
                rerun_match.group(1).lower() == "true" if rerun_match else False
            ),
            "reason": reason_match.group(1) if reason_match else "No reason provided",
            "critique": (
                critique_match.group(1) if critique_match else "No critique provided"
            ),
            "market_alignment": (
                market_alignment_match.group(1)
                if market_alignment_match
                else "No market alignment information provided"
            ),
            "prompt_update": update_match.group(1) if update_match else "",
        }

        # Ensure consistency between verdict and require_rerun
        if decision["verdict"] == "RETRY" and not decision["require_rerun"]:
            decision["require_rerun"] = True

        return decision

    def suggest_reroute(
        self,
        user_prompt: str,
        system_prompt: str,
        solver_results: List[Dict[str, Any]],
        attempted_solvers: List[str],
        all_available_solvers: List[str],
        max_solver_attempts: int = 3,
        model: str = "gpt-4-turbo",
    ) -> Dict[str, Any]:
        """
        Analyze solver failures and recommend re-routing with modified solver selection.

        Args:
            user_prompt: The original user prompt
            system_prompt: The system prompt
            solver_results: List of results from attempted solvers
            attempted_solvers: List of solvers that have been tried
            all_available_solvers: List of all available solvers
            max_solver_attempts: Maximum number of attempts per solver
            model: The ChatGPT model to use

        Returns:
            Dictionary containing:
                - 'should_reroute': Boolean indicating whether to re-route
                - 'excluded_solvers': List of solvers to exclude from next routing
                - 'routing_guidance': Additional guidance for the router
                - 'reason': Reason for the re-routing recommendation
        """
        self.logger.info(
            "Analyzing solver results to determine if re-routing is needed"
        )

        # Default response structure
        result = {
            "should_reroute": False,
            "excluded_solvers": [],
            "routing_guidance": "",
            "reason": "No re-routing needed",
        }

        # Check for market contradictions first 
        for solver_result in solver_results:
            overseer_result = solver_result.get("overseer_result", {})
            overseer_decision = overseer_result.get("decision", {})
            market_alignment = overseer_decision.get("market_alignment", "")
            recommendation = solver_result.get("recommendation", "")
            
            # If market strongly contradicts solver and we have multiple attempts
            if ("STRONGLY" in market_alignment and 
                "contradicts" in market_alignment.lower() or 
                "does not align" in market_alignment.lower() or
                "not align" in market_alignment.lower()) and len(solver_results) > 1:
                
                solver_name = solver_result.get("solver", "unknown")
                # If the same solver has given the same contradicting result multiple times
                consistent_contradiction = False
                contradicting_results = 0
                
                for r in solver_results:
                    if r.get("solver") == solver_name and r.get("recommendation") == recommendation:
                        contradicting_results += 1
                
                if contradicting_results >= 2:
                    # This solver consistently contradicts market sentiment
                    self.logger.info(
                        f"Solver {solver_name} consistently contradicts strong market sentiment ({contradicting_results} times)"
                    )
                    
                    result["should_reroute"] = True
                    result["excluded_solvers"].append(solver_name)
                    result["routing_guidance"] = f"The {solver_name} solver has repeatedly produced results that contradict strong market signals. Try other solvers or a combination approach."
                    result["reason"] = f"Multiple contradictions ({contradicting_results}) between {solver_name} solver and strong market sentiment."
                    
                    # No need to check other criteria, return immediately
                    return result

        # Check if any solvers have consistently failed
        failing_solvers = []
        for solver_name in attempted_solvers:
            # Count attempts and failures for this solver
            solver_attempts = [
                r for r in solver_results if r.get("solver") == solver_name
            ]
            failed_attempts = [
                r
                for r in solver_attempts
                if r.get("solver_result", {}).get("recommendation") == "p4"
                or not r.get("execution_successful", True)
            ]

            # If the solver has failed consistently, add to failing solvers
            if len(failed_attempts) >= min(len(solver_attempts), max_solver_attempts):
                failing_solvers.append(solver_name)
                self.logger.info(
                    f"Solver {solver_name} has failed consistently ({len(failed_attempts)}/{len(solver_attempts)})"
                )

        # If no consistently failing solvers, return default
        if not failing_solvers:
            return result

        # Check if there are alternative solvers available
        available_alternatives = [
            s for s in all_available_solvers if s not in failing_solvers
        ]
        if not available_alternatives:
            self.logger.info(
                "No alternative solvers available, must continue with existing solvers"
            )
            return result

        # Prepare a prompt for ChatGPT to analyze the situation
        reroute_prompt = f"""You are an expert overseer for UMA's optimistic oracle system. You need to analyze solver performance and recommend re-routing strategy.

ORIGINAL QUERY:
{user_prompt}

SOLVER PERFORMANCE SUMMARY:
"""

        # Add summary of each solver's performance
        for solver_name in attempted_solvers:
            solver_attempts = [
                r for r in solver_results if r.get("solver") == solver_name
            ]
            reroute_prompt += f"\n{solver_name.upper()} SOLVER:"

            for i, attempt in enumerate(solver_attempts):
                success = attempt.get("execution_successful", False)
                recommendation = attempt.get("recommendation", "unknown")
                status = (
                    "✅ SUCCESS" if success and recommendation != "p4" else "❌ FAILURE"
                )
                reroute_prompt += (
                    f"\n- Attempt {i+1}: {status} - Recommendation: {recommendation}"
                )

                # Add more details for code_runner solver
                if solver_name == "code_runner":
                    # Add code output if available
                    if "code_output" in attempt.get("solver_result", {}):
                        output_snippet = attempt.get("solver_result", {}).get(
                            "code_output", ""
                        )
                        if output_snippet:
                            # Truncate long outputs
                            if len(output_snippet) > 200:
                                output_snippet = output_snippet[:200] + "..."
                            reroute_prompt += f"\n  Output: {output_snippet}"
                    
                    # Add code itself for analysis
                    if "code" in attempt.get("solver_result", {}):
                        code_snippet = attempt.get("solver_result", {}).get(
                            "code", ""
                        )
                        if code_snippet:
                            # Extract the critical parts like dates and variable definitions
                            import re
                            date_patterns = re.findall(r'date\d*\s*=\s*["\'](\d{4}-\d{2}-\d{2})["\']', code_snippet)
                            if date_patterns:
                                reroute_prompt += f"\n  Dates in code: {', '.join(date_patterns)}"
                            
                            # Add info about the market description from user prompt to check date consistency
                            query_snippet = user_prompt[:500] if len(user_prompt) > 500 else user_prompt
                            market_dates = re.findall(r'(\d{2}\s*[A-Za-z]{3}\s*[\']?\d{2})', query_snippet)
                            if market_dates:
                                reroute_prompt += f"\n  Dates in market description: {', '.join(market_dates)}"

        reroute_prompt += f"""

FAILING SOLVERS: {', '.join(failing_solvers)}
AVAILABLE ALTERNATIVE SOLVERS: {', '.join(available_alternatives)}

Based on the above information, please analyze whether we should:
1. Exclude certain failing solvers from the next routing decision
2. Provide specific guidance to the router on how to better route this query

Return your analysis in a specific format:
```decision
{{
  "should_reroute": true/false,
  "excluded_solvers": ["solver1", "solver2"],
  "routing_guidance": "Brief specific guidance for the router",
  "reason": "Detailed explanation of your recommendation"
}}
```
"""

        # Query ChatGPT
        raw_response = query_chatgpt(
            prompt=reroute_prompt,
            api_key=self.api_key,
            model=model,
            verbose=self.verbose,
        )

        # Extract response text
        response_text = raw_response.choices[0].message.content

        # Extract the routing decision
        import json
        import re

        decision_pattern = r"```decision\s*(\{[\s\S]*?\})\s*```"
        match = re.search(decision_pattern, response_text)

        if match:
            try:
                decision = json.loads(match.group(1))

                # Validate the decision
                should_reroute = decision.get("should_reroute", False)
                excluded_solvers = decision.get("excluded_solvers", [])
                routing_guidance = decision.get("routing_guidance", "")
                reason = decision.get("reason", "")

                # Validate excluded solvers
                excluded_solvers = [
                    s for s in excluded_solvers if s in attempted_solvers
                ]

                result = {
                    "should_reroute": should_reroute,
                    "excluded_solvers": excluded_solvers,
                    "routing_guidance": routing_guidance,
                    "reason": reason,
                }

                self.logger.info(
                    f"Re-routing recommendation: should_reroute={should_reroute}, excluded_solvers={excluded_solvers}"
                )

            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing re-routing decision JSON: {e}")

        return result
