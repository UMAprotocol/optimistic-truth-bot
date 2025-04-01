#!/usr/bin/env python3
"""
Router implementation for UMA Multi-Operator System.
Decides which solver to use for a given proposal.
"""

import logging
from typing import Dict, Any, List, Optional

from ..common import query_chatgpt


class Router:
    """
    Router for UMA Multi-Operator System.
    Decides which solver to use for a given proposal based on ChatGPT analysis.
    """

    def __init__(self, api_key: str, verbose: bool = False):
        """
        Initialize the router.

        Args:
            api_key: OpenAI API key for ChatGPT
            verbose: Whether to print verbose output
        """
        self.api_key = api_key
        self.verbose = verbose
        self.logger = logging.getLogger("router")

        # List of available solvers
        self.available_solvers = ["perplexity"]

    def get_router_prompt(
        self, user_prompt: str, available_solvers: Optional[List[str]] = None
    ) -> str:
        """
        Generate the router prompt for ChatGPT to decide which solver to use.

        Args:
            user_prompt: The user prompt to analyze
            available_solvers: List of available solvers (defaults to self.available_solvers)

        Returns:
            The router prompt for ChatGPT
        """
        if available_solvers is None:
            available_solvers = self.available_solvers

        solvers_str = ", ".join(available_solvers)

        prompt = f"""You are an expert router for UMA's optimistic oracle system. Your task is to analyze the provided query and decide which AI solver is best suited to handle it.

Available solvers: {solvers_str}

USER PROMPT:
{user_prompt}

Please analyze the prompt carefully, considering:
1. The complexity of the query
2. The type of information needed
3. Whether the question requires specialized knowledge
4. Any other relevant factors

Based on your analysis, determine the most appropriate solver from the available options.

IMPORTANT: Return your answer in a specific format:
```decision
{{
  "solver": "[solver_name]",
  "reason": "Brief explanation of why this solver is best suited"
}}
```

Where:
- solver_name: The name of the chosen solver from {solvers_str}
- reason: A brief explanation of why you selected this solver

For now, since we only have Perplexity available, you should generally choose it. However, your analysis is still important as it will help inform future solver selection capabilities.
"""
        return prompt

    def route(
        self,
        user_prompt: str,
        available_solvers: Optional[List[str]] = None,
        model: str = "gpt-4-turbo",
    ) -> Dict[str, Any]:
        """
        Route a proposal to the appropriate solver.

        Args:
            user_prompt: The user prompt to route
            available_solvers: List of available solvers (defaults to self.available_solvers)
            model: The ChatGPT model to use for routing

        Returns:
            Dictionary containing:
                - 'solver': The chosen solver name
                - 'reason': The reason for choosing the solver
                - 'response': The response text from ChatGPT
        """
        if available_solvers is None:
            available_solvers = self.available_solvers

        self.logger.info("Routing proposal to appropriate solver")
        if self.verbose:
            print("Routing proposal to appropriate solver...")
            print(f"Available solvers: {', '.join(available_solvers)}")

        # Generate the router prompt
        router_prompt = self.get_router_prompt(
            user_prompt=user_prompt,
            available_solvers=available_solvers,
        )

        # Query ChatGPT API
        raw_response = query_chatgpt(
            prompt=router_prompt,
            api_key=self.api_key,
            model=model,
            verbose=self.verbose,
        )

        # Extract response text
        response_text = raw_response.choices[0].message.content

        # Extract the routing decision
        decision = self.extract_decision(response_text, available_solvers)

        if self.verbose:
            print(f"Selected solver: {decision.get('solver', 'perplexity')}")
            print(f"Reason: {decision.get('reason', 'Default selection')}")

        self.logger.info(f"Selected solver: {decision.get('solver', 'perplexity')}")

        return {
            "solver": decision.get("solver", "perplexity"),
            "reason": decision.get("reason", "Default selection"),
            "response": response_text,
        }

    def extract_decision(
        self, response_text: str, available_solvers: List[str]
    ) -> Dict[str, Any]:
        """
        Extract the routing decision from the ChatGPT response.

        Args:
            response_text: The response text from ChatGPT
            available_solvers: List of available solvers

        Returns:
            Dictionary containing the solver and reason
        """
        import re
        import json

        # Look for a decision block in the format:
        # ```decision
        # {
        #   "solver": "perplexity",
        #   "reason": "Perplexity is best suited because..."
        # }
        # ```
        decision_pattern = r"```decision\s*(\{[\s\S]*?\})\s*```"
        match = re.search(decision_pattern, response_text)

        if match:
            try:
                decision = json.loads(match.group(1))
                # Validate the solver
                if "solver" in decision and decision["solver"] in available_solvers:
                    return decision
                else:
                    self.logger.warning(
                        f"Invalid solver in decision: {decision.get('solver')}"
                    )
                    return {
                        "solver": "perplexity",
                        "reason": "Default selection (invalid solver in decision)",
                    }
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing decision JSON: {e}")
                return self.extract_decision_fallback(response_text, available_solvers)

        return self.extract_decision_fallback(response_text, available_solvers)

    def extract_decision_fallback(
        self, response_text: str, available_solvers: List[str]
    ) -> Dict[str, Any]:
        """
        Fallback method to extract decision information from the ChatGPT response
        if the JSON format is not found or invalid.

        Args:
            response_text: The response text from ChatGPT
            available_solvers: List of available solvers

        Returns:
            Dictionary containing the solver and reason
        """
        import re

        # Look for solver name patterns
        solver_pattern = r"(?:solver|choose|select|use):\s*(\w+)"
        solver_match = re.search(solver_pattern, response_text, re.IGNORECASE)

        # Look for reason patterns
        reason_pattern = r"(?:reason|explanation|because):\s*([^\n]+)"
        reason_match = re.search(reason_pattern, response_text, re.IGNORECASE)

        # Direct mention of solver name
        solver = None
        if solver_match:
            solver_candidate = solver_match.group(1).lower()
            if solver_candidate in available_solvers:
                solver = solver_candidate

        # If no valid solver found, look for direct mentions of solver names in the text
        if not solver:
            for available_solver in available_solvers:
                if available_solver.lower() in response_text.lower():
                    solver = available_solver
                    break

        # Default to perplexity if still no valid solver
        if not solver or solver not in available_solvers:
            solver = "perplexity"

        reason = (
            reason_match.group(1)
            if reason_match
            else "Default selection based on available solvers"
        )

        return {"solver": solver, "reason": reason}
