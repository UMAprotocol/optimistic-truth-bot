#!/usr/bin/env python3
"""
Overseer implementation for UMA Multi-Operator System.
Provides validation and feedback on solver responses.
"""

import logging
import json
import re
from typing import Dict, Any, Optional, Tuple

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
            "prompt_update": update_match.group(1) if update_match else "",
        }

        # Ensure consistency between verdict and require_rerun
        if decision["verdict"] == "RETRY" and not decision["require_rerun"]:
            decision["require_rerun"] = True

        return decision
