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
        self.available_solvers = ["perplexity", "code_runner"]

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
        if available_solvers is None:
            available_solvers = self.available_solvers

        # If excluded_solvers is provided, filter available_solvers
        if excluded_solvers:
            available_solvers = [
                s for s in available_solvers if s not in excluded_solvers
            ]

        # Ensure we have at least one solver
        if not available_solvers:
            self.logger.warning(
                "No available solvers after exclusions, using perplexity as fallback"
            )
            available_solvers = ["perplexity"]

        solvers_str = ", ".join(available_solvers)

        prompt = f"""You are an expert router for UMA's optimistic oracle system. Your task is to analyze the provided query and decide which AI solver is best suited to handle it.

Available solvers: {solvers_str}

Solver descriptions:
- perplexity: Uses the Perplexity AI search engine to find information online to answer general questions. Best for:
  * Historical data and events
  * General knowledge questions requiring context
  * Questions needing interpretation of complex information
  * Has knowledge cutoff and may not have very recent information

- code_runner: Executes code to fetch real-time data from specific APIs. Currently supports:
  * Binance API: Can fetch cryptocurrency prices at specific times/dates with timezone conversion
  * Sports Data IO: Can retrieve MLB game results, scores, team performance and game status
  * Best for questions requiring precise, current data from these specific sources
  * Limited to only these data sources - cannot access other APIs or general information

USER PROMPT:
{user_prompt}

Please analyze the prompt carefully, considering:
1. The complexity of the query
2. The type of information needed
3. Whether the question requires specialized knowledge or data access
4. Whether the question specifically involves cryptocurrency prices or MLB sports data
5. Whether multiple approaches might be complementary

IMPORTANT: You SHOULD select MULTIPLE solvers when appropriate. For complementary approaches, multiple solvers can provide different perspectives on the same question.
"""

        # Add overseer guidance if provided
        if overseer_guidance:
            prompt += f"""
OVERSEER GUIDANCE:
Based on previous attempts to solve this question, the overseer has provided the following guidance:
{overseer_guidance}

Please take this guidance into account when making your decision.
"""

        # If there are excluded solvers, explain why
        if excluded_solvers:
            excluded_str = ", ".join(excluded_solvers)
            prompt += f"""
NOTE: The following solvers have been EXCLUDED due to previous failures or overseer feedback: {excluded_str}
"""

        prompt += """
Return your answer in a specific format:
```decision
{
  "solvers": ["solver_name1", "solver_name2"],
  "reason": "Brief explanation of why these solvers are best suited",
  "multi_solver_strategy": "Optional explanation of how these solvers complement each other"
}
```

Where:
- solvers: Array of solver names selected from the available solvers
- reason: A brief explanation of why you selected these solvers
- multi_solver_strategy: If multiple solvers are selected, explain how they complement each other

Guidelines for solver selection:
- Use code_runner when the question specifically asks for:
  * Current or historical cryptocurrency prices from Binance (e.g., "What was the price of BTC on March 30th at 12pm ET?")
  * MLB game results, scores or team performance (e.g., "Did the Blue Jays win against the Orioles on April 1st?")
  
- Use perplexity when the question requires:
  * General knowledge or context not limited to specific data points
  * Explanation or interpretation of events, rules, or concepts
  * Information beyond just crypto prices or MLB sports data
  
- Use both solvers when:
  * The question needs both factual data AND context/interpretation
  * Example: "Did BTC price increase after the news about XYZ on March 30th?" (code_runner for price data, perplexity for news context)
  * Example: "How did the Blue Jays perform compared to expectations in their April 1st game?" (code_runner for game data, perplexity for context about expectations)

Remember: code_runner is highly accurate for the supported data types but limited in scope. Perplexity has broader knowledge but may not have the most current information.
"""
        return prompt

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
        if available_solvers is None:
            available_solvers = self.available_solvers

        # Apply exclusions
        if excluded_solvers:
            effective_solvers = [
                s for s in available_solvers if s not in excluded_solvers
            ]
            if not effective_solvers:
                self.logger.warning(
                    "No available solvers after exclusions, using perplexity as fallback"
                )
                effective_solvers = ["perplexity"]
        else:
            effective_solvers = available_solvers

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
