#!/usr/bin/env python3
"""
Base solver interface for UMA Multi-Operator System.
All solvers should inherit from this base class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseSolver(ABC):
    """
    Abstract base class for all solvers in the UMA Multi-Operator System.
    """

    def __init__(self, api_key: str, verbose: bool = False):
        """
        Initialize the solver.

        Args:
            api_key: API key for the solver
            verbose: Whether to print verbose output
        """
        self.api_key = api_key
        self.verbose = verbose

    @abstractmethod
    def solve(
        self, user_prompt: str, system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Solve a proposal using the solver's specific logic.

        Args:
            user_prompt: The user prompt to solve
            system_prompt: Optional system prompt to use

        Returns:
            Dictionary containing:
                - 'recommendation': The recommendation (p1, p2, p3, p4)
                - 'response': The full response from the solver
                - 'raw_response': The raw response object from the API
                - Other solver-specific data
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Get the name of the solver.

        Returns:
            The name of the solver
        """
        pass
