#!/usr/bin/env python3
"""
Perplexity solver implementation for UMA Multi-Operator System.
"""

import logging
import time
from datetime import datetime  
from typing import Dict, Any, Optional

from .base_solver import BaseSolver
from ..common import query_perplexity, extract_recommendation
from ..prompts.perplexity_prompt import get_system_prompt, create_messages


class PerplexitySolver(BaseSolver):
    """
    Perplexity solver implementation for UMA Multi-Operator System.
    Uses the Perplexity API to solve proposals.
    """

    def __init__(self, api_key: str, verbose: bool = False):
        """
        Initialize the Perplexity solver.

        Args:
            api_key: Perplexity API key
            verbose: Whether to print verbose output
        """
        super().__init__(api_key, verbose)
        self.logger = logging.getLogger("perplexity_solver")

    def solve(
        self, user_prompt: str, system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Solve a proposal using the Perplexity API.

        Args:
            user_prompt: The user prompt to solve
            system_prompt: Optional system prompt to use

        Returns:
            Dictionary containing:
                - 'recommendation': The recommendation (p1, p2, p3, p4)
                - 'response': The full response from Perplexity
                - 'solver': The name of the solver
                - 'response_metadata': Metadata about the response (timing, tokens, etc.)
        """
        self.logger.info("Solving proposal with Perplexity")
        if self.verbose:
            print("Solving proposal with Perplexity...")

        # Record start time for timing
        start_time = time.time()

        # If no system prompt provided, use the default from perplexity_prompt
        if not system_prompt:
            system_prompt = get_system_prompt()

        try:
            # Query Perplexity API
            raw_response = query_perplexity(
                prompt=user_prompt,
                api_key=self.api_key,
                system_prompt=system_prompt,
                verbose=self.verbose,
            )

            # Calculate elapsed time
            elapsed_time = time.time() - start_time

            # Check if the response contains an error
            if isinstance(raw_response, dict) and "error" in raw_response:
                error_message = raw_response.get("error", "Unknown API error")
                self.logger.error(f"Perplexity API error: {error_message}")
                
                # Return a structured error response
                return {
                    "recommendation": "p4",  # Default to p4 when we encounter API errors
                    "response": f"Error: Unable to complete request due to API error: {error_message}",
                    "solver": self.get_name(),
                    "response_metadata": {
                        "execution_successful": False,
                        "error": error_message,
                        "api_response_time_seconds": elapsed_time,
                        "created_timestamp": int(time.time()),
                        "created_datetime": datetime.fromtimestamp(time.time()).strftime("%Y-%m-%dT%H:%M:%S"),
                        "failure_reason": f"API error: {error_message}"
                    },
                }

            # Extract response text and recommendation
            response_text = raw_response.choices[0].message.content
            recommendation = extract_recommendation(response_text)

            if self.verbose:
                print(f"Perplexity recommendation: {recommendation}")
                print("-" * 40)
                print("Response text:")
                print(response_text)
                print("-" * 40)

            self.logger.info(f"Perplexity recommendation: {recommendation}")

            # Extract token usage info if available
            response_metadata = {
                "model": raw_response.model,
                "created_timestamp": int(raw_response.created),
                "created_datetime": datetime.fromtimestamp(raw_response.created).strftime(
                    "%Y-%m-%dT%H:%M:%S"
                ),
                "api_response_time_seconds": elapsed_time,
                "execution_successful": True,
            }

            # Add token usage if available
            if hasattr(raw_response, "usage"):
                response_metadata.update(
                    {
                        "completion_tokens": raw_response.usage.completion_tokens,
                        "prompt_tokens": raw_response.usage.prompt_tokens,
                        "total_tokens": raw_response.usage.total_tokens,
                    }
                )

            return {
                "recommendation": recommendation,
                "response": response_text,
                "solver": self.get_name(),
                "response_metadata": response_metadata,
            }
        
        except Exception as e:
            # Calculate elapsed time for error case
            elapsed_time = time.time() - start_time
            
            error_message = f"Error during Perplexity API call: {str(e)}"
            self.logger.error(error_message)
            
            # Return a structured error response
            return {
                "recommendation": "p4",  # Default to p4 when we encounter API errors
                "response": f"Error: Unable to complete request: {str(e)}",
                "solver": self.get_name(),
                "response_metadata": {
                    "execution_successful": False,
                    "error": str(e),
                    "api_response_time_seconds": elapsed_time,
                    "created_timestamp": int(time.time()),
                    "created_datetime": datetime.fromtimestamp(time.time()).strftime("%Y-%m-%dT%H:%M:%S"),
                    "failure_reason": f"Exception: {str(e)}"
                },
            }

    def get_name(self) -> str:
        """
        Get the name of the solver.

        Returns:
            The name of the solver
        """
        return "perplexity"