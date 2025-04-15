#!/usr/bin/env python3
"""
Router implementation for UMA Multi-Operator System.
Decides which solver to use for a given proposal.
"""

import logging
from typing import Dict, Any, List, Optional

from ..common import query_chatgpt
from ..prompts.router_prompt import get_router_prompt


class Router:
    """
    Router for UMA Multi-Operator System.
    Decides which solver to use for a given proposal based on ChatGPT analysis.
    """

    def __init__(
        self, 
        api_key: str, 
        verbose: bool = False, 
        available_api_keys: Optional[List[str]] = None,
        data_sources: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the router.

        Args:
            api_key: OpenAI API key for ChatGPT
            verbose: Whether to print verbose output
            available_api_keys: List of API keys available to the code_runner
            data_sources: Dictionary of data sources with their detailed configuration
        """
        self.api_key = api_key
        self.verbose = verbose
        self.logger = logging.getLogger("router")
        
        # Store available API keys
        self.available_api_keys = available_api_keys or []
        
        # Store data sources
        self.data_sources = data_sources or {}

        # List of available solvers
        self.available_solvers = ["perplexity", "code_runner"]
        
        # Log the available data sources
        if self.data_sources and self.verbose:
            self.logger.info(f"Router initialized with {len(self.data_sources)} data sources")
            for source_name, source in self.data_sources.items():
                category = source.get("category", "unknown")
                self.logger.info(f"  - {source_name} ({category})")

    def get_router_prompt(
        self,
        user_prompt: str,
        available_solvers: Optional[List[str]] = None,
        excluded_solvers: Optional[List[str]] = None,
        overseer_guidance: Optional[str] = None,
    ) -> str:
        """
        Generate the router prompt for ChatGPT to decide which solver to use.

        Args:
            user_prompt: The user prompt to analyze
            available_solvers: List of available solvers (defaults to self.available_solvers)
            excluded_solvers: List of solvers to exclude from consideration
            overseer_guidance: Additional guidance from the overseer

        Returns:
            The router prompt for ChatGPT
        """
        # Get effective solvers after applying exclusions
        effective_solvers = self._filter_solvers(available_solvers, excluded_solvers)

        # Use the router prompt from the prompts module
        return get_router_prompt(
            user_prompt=user_prompt,
            available_solvers=effective_solvers,
            excluded_solvers=excluded_solvers,
            overseer_guidance=overseer_guidance,
            data_sources=self.data_sources,
            available_api_keys=self.available_api_keys,
            verbose=self.verbose
        )

    def _filter_solvers(self, available_solvers, excluded_solvers):
        """
        Filter available solvers based on exclusions.
        
        Args:
            available_solvers: List of available solvers
            excluded_solvers: List of solvers to exclude
            
        Returns:
            List of effective solvers after applying exclusions
        """
        if available_solvers is None:
            available_solvers = self.available_solvers
            
        if not excluded_solvers:
            return available_solvers
            
        effective_solvers = [
            s for s in available_solvers if s not in excluded_solvers
        ]
        
        if not effective_solvers:
            self.logger.warning(
                "No available solvers after exclusions, using perplexity as fallback"
            )
            return ["perplexity"]
            
        return effective_solvers

    def route(
        self,
        user_prompt: str,
        available_solvers: Optional[List[str]] = None,
        excluded_solvers: Optional[List[str]] = None,
        overseer_guidance: Optional[str] = None,
        model: str = "gpt-4-turbo",
    ) -> Dict[str, Any]:
        """
        Route a proposal to the appropriate solver(s).

        Args:
            user_prompt: The user prompt to route
            available_solvers: List of available solvers (defaults to self.available_solvers)
            excluded_solvers: List of solvers to exclude from consideration
            overseer_guidance: Additional guidance from the overseer
            model: The ChatGPT model to use for routing

        Returns:
            Dictionary containing:
                - 'solvers': List of chosen solver names
                - 'reason': The reason for choosing the solvers
                - 'multi_solver_strategy': Strategy for using multiple solvers (if applicable)
                - 'response': The response text from ChatGPT
        """
        # Get effective solvers after applying exclusions
        effective_solvers = self._filter_solvers(available_solvers, excluded_solvers)

        self.logger.info("Routing proposal to appropriate solver(s)")
        if self.verbose:
            print("Routing proposal to appropriate solver(s)...")
            print(f"Available solvers: {', '.join(effective_solvers)}")
            if excluded_solvers:
                print(f"Excluded solvers: {', '.join(excluded_solvers)}")
            if overseer_guidance:
                print(f"With overseer guidance: {overseer_guidance}")

        # Generate the router prompt
        router_prompt = self.get_router_prompt(
            user_prompt=user_prompt,
            available_solvers=effective_solvers,
            excluded_solvers=excluded_solvers,
            overseer_guidance=overseer_guidance,
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
        decision = self.extract_decision(response_text, effective_solvers)

        if self.verbose:
            print(f"Selected solvers: {decision.get('solvers', ['perplexity'])}")
            print(f"Reason: {decision.get('reason', 'Default selection')}")
            if (
                "multi_solver_strategy" in decision
                and decision["multi_solver_strategy"]
            ):
                print(f"Multi-solver strategy: {decision['multi_solver_strategy']}")

        self.logger.info(f"Selected solvers: {decision.get('solvers', ['perplexity'])}")
        if len(decision.get("solvers", [])) > 1:
            self.logger.info(
                f"Multi-solver strategy: {decision.get('multi_solver_strategy', 'No strategy provided')}"
            )

        return {
            "solvers": decision.get("solvers", ["perplexity"]),
            "reason": decision.get("reason", "Default selection"),
            "multi_solver_strategy": decision.get("multi_solver_strategy", ""),
            "response": response_text,
            "prompt": router_prompt  # Save the router prompt for debugging
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
            Dictionary containing the solvers and reason
        """
        import re
        import json

        # Look for a decision block in the format:
        # ```decision
        # {
        #   "solvers": ["perplexity", "code_runner"],
        #   "reason": "Perplexity is best suited because...",
        #   "multi_solver_strategy": "These solvers complement each other because..."
        # }
        # ```
        decision_pattern = r"```decision\s*(\{[\s\S]*?\})\s*```"
        match = re.search(decision_pattern, response_text)

        if match:
            try:
                decision = json.loads(match.group(1))
                # Validate the solvers
                if "solvers" in decision and isinstance(decision["solvers"], list):
                    # Filter out any invalid solvers
                    decision["solvers"] = [
                        solver
                        for solver in decision["solvers"]
                        if solver in available_solvers
                    ]
                    # If we have at least one valid solver, return the decision
                    if decision["solvers"]:
                        return decision

                # If we get here, there were no valid solvers in the decision
                self.logger.warning(
                    f"No valid solvers in decision: {decision.get('solvers')}"
                )
                return {
                    "solvers": ["perplexity"],
                    "reason": "Default selection (no valid solvers in decision)",
                    "multi_solver_strategy": "",
                }
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing decision JSON: {e}")
                return self.extract_decision_fallback(response_text, available_solvers)

        # If no decision block is found, try the fallback method
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
            Dictionary containing the solvers and reason
        """
        import re

        # List to store the solvers mentioned in the response
        mentioned_solvers = []

        # Look for mentions of available solvers in the response text
        for solver in available_solvers:
            if solver.lower() in response_text.lower():
                mentioned_solvers.append(solver)

        # If no solvers were explicitly mentioned, default to perplexity
        if not mentioned_solvers:
            mentioned_solvers = ["perplexity"]

        # Look for reason patterns
        reason_pattern = r"(?:reason|explanation|because):\s*([^\n]+)"
        reason_match = re.search(reason_pattern, response_text, re.IGNORECASE)

        # Extract reason or provide a default
        reason = (
            reason_match.group(1)
            if reason_match
            else "Default selection based on available solvers"
        )

        # Look for multi-solver strategy
        strategy_pattern = r"(?:strategy|approach|method|how to use):\s*([^\n]+)"
        strategy_match = re.search(strategy_pattern, response_text, re.IGNORECASE)

        strategy = strategy_match.group(1) if strategy_match else ""

        return {
            "solvers": mentioned_solvers,
            "reason": reason,
            "multi_solver_strategy": strategy,
        }
