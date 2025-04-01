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
from datetime import datetime
from pathlib import Path
import logging
from dotenv import load_dotenv
import signal
import importlib

# Import local modules
from .common import (
    setup_logging,
    format_prompt_from_json,
    get_query_id_from_proposal,
    get_question_id_short,
    get_output_filename,
    should_process_proposal,
    get_token_price,
)
from .router.router import Router
from .overseer.overseer import Overseer
from .solvers.perplexity_solver import PerplexitySolver
from .overseer.prompt_overseer import format_market_price_info


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
        """
        # Load environment variables
        load_dotenv()
        self.verbose = verbose

        # Set up logging
        self.logger = setup_logging(
            "multi_operator_processor", "logs/multi_operator_processor.log"
        )

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

        # Load solver system prompt
        self.load_solver_prompt()

        # Track processed files to avoid duplicate processing
        self.processed_files = set()

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

    def load_solver_prompt(self):
        """Load the solver system prompt from the prompt.py module."""
        try:
            # Dynamically import the prompt module
            prompt_module = importlib.import_module("prompt")
            self.get_system_prompt = getattr(prompt_module, "get_system_prompt")
            self.logger.info("Successfully loaded system prompt from prompt.py")
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

    def initialize_components(self):
        """Initialize the router, solver, and overseer components."""
        self.logger.info("Initializing components")

        # Initialize router
        self.router = Router(api_key=self.openai_api_key, verbose=self.verbose)
        self.logger.info("Router initialized")

        # Initialize solvers
        self.solvers = {
            "perplexity": PerplexitySolver(
                api_key=self.perplexity_api_key, verbose=self.verbose
            )
        }
        self.logger.info(f"Initialized {len(self.solvers)} solvers")

        # Initialize overseer
        self.overseer = Overseer(api_key=self.openai_api_key, verbose=self.verbose)
        self.logger.info("Overseer initialized")

    def scan_proposals(self):
        """Scan for new proposals in the proposals directory."""
        self.logger.info(f"Scanning for proposals in {self.proposals_dir}")

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
                tokens = proposal_obj.get("tokens", [])
                self.logger.info(f"Found {len(tokens)} tokens in proposal data")

                # Update token prices from Polymarket API
                for token in tokens:
                    # Check if shutdown was requested
                    if hasattr(self, "shutdown_requested") and self.shutdown_requested:
                        self.logger.info(
                            f"Skipping token price fetch - shutdown requested"
                        )
                        break

                    token_id = token.get("token_id")
                    # Skip price fetching if we already have winner information or price is set to 1
                    if token.get("winner") is not None or token.get("price") == 1:
                        self.logger.info(
                            f"Skipping price fetch for token {token_id} - already have winner info or price=1"
                        )
                        continue

                    if token_id:
                        self.logger.info(f"Fetching price for token {token_id}")
                        price_data = get_token_price(token_id, verbose=self.verbose)
                        if price_data and "price" in price_data:
                            # Update the token price with the latest data
                            token["price"] = price_data["price"]
                            self.logger.info(
                                f"Updated token {token_id} price to {price_data['price']}"
                            )

            # Format user prompt
            user_prompt = format_prompt_from_json(proposal_data)
            system_prompt = self.get_system_prompt()

            # Route the proposal to determine which solver to use
            self.logger.info(f"Routing proposal {short_id} to determine solver")
            routing_result = self.router.route(user_prompt=user_prompt)
            solver_name = routing_result["solver"]

            self.logger.info(f"Router selected solver: {solver_name}")
            if self.verbose:
                print(f"Router selected solver: {solver_name}")
                print(f"Reason: {routing_result['reason']}")

            # Process the proposal with the selected solver and overseer
            solver_overseer_result = self.process_with_solver_and_overseer(
                solver_name=solver_name,
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                tokens=tokens,
            )

            # Initialize a comprehensive result object with all fields from the proposal
            result = {
                # Basic identification fields
                "query_id": query_id,
                "short_id": short_id,
                "file_path": str(file_path),
                "processed_file": file_path.name,
                # Core recommendation fields
                "recommendation": solver_overseer_result["recommendation"],
                "total_attempts": solver_overseer_result["total_attempts"],
                "attempts": solver_overseer_result["attempts"],
                # Timestamps and metadata
                "timestamp": time.time(),
                # Router decision
                "router_decision": {
                    "solver": routing_result["solver"],
                    "reason": routing_result["reason"],
                },
                # Add prompts for reference
                "user_prompt": user_prompt,
                "system_prompt": system_prompt,
            }

            # Add pricing information if available
            if "proposed_price" in proposal_obj:
                result["proposed_price"] = proposal_obj.get("proposed_price")
            if "resolved_price" in proposal_obj:
                result["resolved_price"] = proposal_obj.get("resolved_price")

            # Add transaction details if available
            if "transaction_hash" in proposal_obj:
                result["transaction_hash"] = proposal_obj.get("transaction_hash")

            # Add resolution information if available
            if "proposed_price_outcome" in proposal_obj:
                result["proposed_price_outcome"] = proposal_obj.get(
                    "proposed_price_outcome"
                )
            if "resolved_price_outcome" in proposal_obj:
                result["resolved_price_outcome"] = proposal_obj.get(
                    "resolved_price_outcome"
                )

            # Add dispute status if available
            if "disputed" in proposal_obj:
                result["disputed"] = proposal_obj.get("disputed")
            else:
                result["disputed"] = False  # Default to false if not specified

            # Add recommendation override status
            result["recommendation_overridden"] = (
                False  # Default value, can be changed later if needed
            )

            # Add condition ID if available
            if "condition_id" in proposal_obj:
                result["condition_id"] = proposal_obj.get("condition_id")

            # Add tags if available
            if "tags" in proposal_obj:
                result["tags"] = proposal_obj.get("tags")

            # Add detailed proposal metadata
            result["proposal_metadata"] = {}
            for key, value in proposal_obj.items():
                if key not in ["query_id", "short_id", "file_path"]:
                    result["proposal_metadata"][key] = value

            # Move specific fields from proposal_metadata to top-level for consistency
            if "proposal_obj" in locals() and proposal_obj:
                for field in ["tags", "icon", "end_date_iso", "game_start_time"]:
                    if field in proposal_obj:
                        result[field] = proposal_obj.get(field)

            # Add detailed overseer data
            result["overseer_data"] = {
                "attempts": solver_overseer_result["total_attempts"],
                "interactions": [],  # Will be filled with interaction details
                "market_price_info": (
                    format_market_price_info(tokens) if tokens else None
                ),
                "tokens": tokens if tokens else [],
                "recommendation_journey": [],  # Will be filled with journey details
            }

            # Fill interactions data
            for attempt_data in solver_overseer_result["attempts"]:
                solver_interaction = {
                    "attempt": attempt_data["attempt"],
                    "response": attempt_data["solver_result"]["response"],
                    "recommendation": attempt_data["solver_result"]["recommendation"],
                    "system_prompt": system_prompt,  # Add original system prompt
                    "cumulative_refinements": False,  # Default value, change if needed
                    "interaction_type": f"{attempt_data['solver']}_query",
                    "stage": (
                        "initial_response"
                        if attempt_data["attempt"] == 1
                        else f"retry_{attempt_data['attempt']}"
                    ),
                }

                # Add response metadata if available
                if "response_metadata" in attempt_data["solver_result"]:
                    solver_interaction["response_metadata"] = attempt_data[
                        "solver_result"
                    ]["response_metadata"]

                # Add overseer evaluation data
                overseer_evaluation = {
                    "interaction_type": "chatgpt_evaluation",
                    "stage": f"evaluation_{attempt_data['attempt']}",
                    "response": attempt_data["overseer_result"].get("response", ""),
                    "satisfaction_level": (
                        "satisfied"
                        if attempt_data["overseer_result"]["verdict"] == "SATISFIED"
                        else "not_satisfied"
                    ),
                    "critique": attempt_data["overseer_result"].get("critique", ""),
                    "decision": attempt_data["overseer_result"]["verdict"].lower(),
                    "require_rerun": attempt_data["overseer_result"]["require_rerun"],
                    "prompt_updated": bool(
                        attempt_data["overseer_result"].get("prompt_update", "")
                    ),
                    "system_prompt_before": system_prompt,
                    "system_prompt_after": system_prompt
                    + (
                        f"\n\nADDITIONAL INSTRUCTIONS: {attempt_data['overseer_result'].get('prompt_update', '')}"
                        if attempt_data["overseer_result"].get("prompt_update", "")
                        else ""
                    ),
                }

                # Add these interactions to the overseer_data
                result["overseer_data"]["interactions"].append(solver_interaction)
                result["overseer_data"]["interactions"].append(overseer_evaluation)

                # Add to recommendation journey
                journey_entry = {
                    "attempt": attempt_data["attempt"],
                    f"{attempt_data['solver']}_recommendation": attempt_data[
                        "solver_result"
                    ]["recommendation"],
                    "overseer_satisfaction_level": (
                        "satisfied"
                        if attempt_data["overseer_result"]["verdict"] == "SATISFIED"
                        else "not_satisfied"
                    ),
                    "prompt_updated": bool(
                        attempt_data["overseer_result"].get("prompt_update", "")
                    ),
                    "critique": attempt_data["overseer_result"].get("critique", ""),
                    "system_prompt_before": system_prompt,
                    "system_prompt_after": system_prompt
                    + (
                        f"\n\nADDITIONAL INSTRUCTIONS: {attempt_data['overseer_result'].get('prompt_update', '')}"
                        if attempt_data["overseer_result"].get("prompt_update", "")
                        else ""
                    ),
                }
                result["overseer_data"]["recommendation_journey"].append(journey_entry)

            # Add final response metadata if available (from the last attempt)
            if solver_overseer_result["attempts"]:
                last_attempt = solver_overseer_result["attempts"][-1]
                if "response_metadata" in last_attempt["solver_result"]:
                    result["overseer_data"]["final_response_metadata"] = last_attempt[
                        "solver_result"
                    ]["response_metadata"]

            # Save the result if output is enabled
            if self.save_output and self.output_dir:
                output_file = self.save_result(result)
                self.logger.info(f"Saved result to {output_file}")

            self.logger.info(f"Completed processing proposal: {short_id}")
            if self.verbose:
                print(f"\n{'='*80}")
                print(f"✅ COMPLETED PROPOSAL: \033[1m\033[36m{short_id}\033[0m")
                print(
                    f"🏆 Final recommendation: \033[1m\033[33m{result.get('recommendation', 'unknown')}\033[0m"
                )
                print(f"🔢 Total attempts: {result.get('total_attempts', 0)}")
                print(f"{'='*80}\n")

            return result

        except KeyboardInterrupt:
            self.logger.warning(
                f"Processing of proposal {short_id} interrupted by user"
            )
            if self.verbose:
                print(
                    f"\n\033[1m\033[33m⚠️ Processing of proposal {short_id} canceled by user\033[0m"
                )

            # Set shutdown flag if it exists
            if hasattr(self, "shutdown_requested"):
                self.shutdown_requested = True

            # Re-raise to be handled by the caller
            raise
        except Exception as e:
            self.logger.error(f"Error processing proposal {short_id}: {e}")
            if self.verbose:
                print(
                    f"\n\033[1m\033[31m❌ Error processing proposal {short_id}: {e}\033[0m"
                )

            # Create a well-formed error result with all required fields
            result = {
                # Basic identification fields
                "query_id": query_id,
                "short_id": short_id,
                "file_path": str(file_path),
                "processed_file": file_path.name,
                "timestamp": time.time(),
                # Error information
                "error": str(e),
                "recommendation": "p4",  # Default to p4 on error
                "total_attempts": 0,
                "attempts": [],
                # Empty fields for consistency
                "overseer_data": {
                    "attempts": 0,
                    "interactions": [],
                    "market_price_info": None,
                    "tokens": [],
                    "recommendation_journey": [],
                },
                # Add router decision if available
                "router_decision": {
                    "solver": "perplexity",  # Default value
                    "reason": f"Error occurred: {str(e)}",
                },
                # Add other required fields
                "user_prompt": user_prompt if "user_prompt" in locals() else "",
                "system_prompt": system_prompt if "system_prompt" in locals() else "",
                "disputed": False,
                "recommendation_overridden": False,
            }

            # Add proposal metadata if available
            if "proposal_obj" in locals() and proposal_obj:
                # Add pricing information if available
                if "proposed_price" in proposal_obj:
                    result["proposed_price"] = proposal_obj.get("proposed_price")
                if "resolved_price" in proposal_obj:
                    result["resolved_price"] = proposal_obj.get("resolved_price")
                if "proposed_price_outcome" in proposal_obj:
                    result["proposed_price_outcome"] = proposal_obj.get(
                        "proposed_price_outcome"
                    )
                if "resolved_price_outcome" in proposal_obj:
                    result["resolved_price_outcome"] = proposal_obj.get(
                        "resolved_price_outcome"
                    )
                if "condition_id" in proposal_obj:
                    result["condition_id"] = proposal_obj.get("condition_id")
                if "tags" in proposal_obj:
                    result["tags"] = proposal_obj.get("tags")

                # Add detailed proposal metadata
                result["proposal_metadata"] = {}
                for key, value in proposal_obj.items():
                    if key not in ["query_id", "short_id", "file_path"]:
                        result["proposal_metadata"][key] = value
            else:
                result["proposal_metadata"] = {}

            # Add proposal fields to the top level if they exist in metadata
            if "proposal_obj" in locals() and proposal_obj:
                for field in ["tags", "icon", "end_date_iso", "game_start_time"]:
                    if field in proposal_obj:
                        result[field] = proposal_obj.get(field)

            # Save the result if output is enabled
            if self.save_output and self.output_dir:
                output_file = self.save_result(result)
                self.logger.info(f"Error result saved to {output_file}")

            return result

    def process_with_solver_and_overseer(
        self, solver_name, user_prompt, system_prompt, tokens=None
    ):
        """
        Process a proposal with the specified solver and overseer.

        Args:
            solver_name: Name of the solver to use
            user_prompt: User prompt to solve
            system_prompt: System prompt to use
            tokens: Optional token objects with price information

        Returns:
            Dictionary containing the processing results
        """
        # Check if the solver exists
        if solver_name not in self.solvers:
            self.logger.error(
                f"Solver {solver_name} not found, using perplexity instead"
            )
            solver_name = "perplexity"

        solver = self.solvers[solver_name]

        attempts = []
        current_attempt = 1
        final_recommendation = None
        updated_system_prompt = system_prompt

        try:
            while current_attempt <= self.max_attempts:
                # Check if shutdown was requested
                if hasattr(self, "shutdown_requested") and self.shutdown_requested:
                    self.logger.info("Stopping solver attempts - shutdown requested")
                    break

                self.logger.info(
                    f"Attempt {current_attempt}/{self.max_attempts} with {solver_name}"
                )
                if self.verbose:
                    attempt_header = f"🔄 ATTEMPT {current_attempt}/{self.max_attempts}"
                    solver_info = f"🤖 Solver: \033[1m\033[36m{solver_name}\033[0m"
                    print(f"\n{'─'*80}")
                    print(f"{attempt_header} | {solver_info}")
                    print(f"{'─'*80}")

                try:
                    # Solve the proposal
                    solver_result = solver.solve(
                        user_prompt=user_prompt, system_prompt=updated_system_prompt
                    )
                except KeyboardInterrupt:
                    self.logger.warning(
                        f"Solver attempt {current_attempt} interrupted by user"
                    )
                    if self.verbose:
                        print(
                            f"\n\033[1m\033[33m⚠️ Solver attempt interrupted by user\033[0m"
                        )
                    if hasattr(self, "shutdown_requested"):
                        self.shutdown_requested = True
                    raise

                recommendation = solver_result["recommendation"]
                solver_response = solver_result["response"]

                self.logger.info(f"Solver recommendation: {recommendation}")
                if self.verbose:
                    print(
                        f"📊 Solver recommendation: \033[1m\033[33m{recommendation}\033[0m"
                    )

                try:
                    # Evaluate the solver's response
                    overseer_result = self.overseer.evaluate(
                        user_prompt=user_prompt,
                        system_prompt=updated_system_prompt,
                        solver_response=solver_response,
                        recommendation=recommendation,
                        attempt=current_attempt,
                        tokens=tokens,
                        solver_name=solver_name,
                    )
                except KeyboardInterrupt:
                    self.logger.warning(f"Overseer evaluation interrupted by user")
                    if self.verbose:
                        print(
                            f"\n\033[1m\033[33m⚠️ Overseer evaluation interrupted by user\033[0m"
                        )
                        if hasattr(self, "shutdown_requested"):
                            self.shutdown_requested = True
                        raise

                decision = overseer_result["decision"]
                verdict = decision.get("verdict", "DEFAULT_TO_P4")
                require_rerun = decision.get("require_rerun", False)

                self.logger.info(
                    f"Overseer verdict: {verdict}, require_rerun: {require_rerun}"
                )

                if self.verbose:
                    # Format verdict with appropriate color and symbol
                    if verdict == "SATISFIED":
                        verdict_display = f"✅ \033[1m\033[32mSATISFIED\033[0m"
                    elif verdict == "RETRY":
                        verdict_display = f"🔄 \033[1m\033[33mRETRY\033[0m"
                    else:
                        verdict_display = f"❌ \033[1m\033[31m{verdict}\033[0m"

                    # Display the verdict and reason
                    print(f"🧐 Overseer verdict: {verdict_display}")
                    if decision.get("reason"):
                        print(f"💭 Reason: {decision.get('reason')}")
                    if require_rerun:
                        print(f"🔁 Requires rerun: \033[1m\033[33mYes\033[0m")
                    print(f"{'─'*80}")

                # Store attempt information (excluding raw API responses that aren't JSON serializable)
                attempts.append(
                    {
                        "attempt": current_attempt,
                        "solver": solver_name,
                        "solver_result": {
                            "recommendation": recommendation,
                            "response": solver_response,
                        },
                        "overseer_result": {
                            "verdict": verdict,
                            "require_rerun": require_rerun,
                            "reason": decision.get("reason", ""),
                            "critique": decision.get("critique", ""),
                            "response": overseer_result.get("response", ""),
                        },
                    }
                )

                # Process the overseer's decision
                if verdict == "SATISFIED":
                    # Overseer is satisfied with the recommendation
                    final_recommendation = recommendation
                    break
                elif (
                    verdict == "RETRY"
                    and require_rerun
                    and current_attempt < self.max_attempts
                ):
                    # Update the system prompt if provided
                    prompt_update = decision.get("prompt_update", "")
                    if prompt_update:
                        updated_system_prompt = f"{updated_system_prompt}\n\nADDITIONAL INSTRUCTIONS: {prompt_update}"
                        self.logger.info("Updated system prompt for next attempt")

                    # Continue to the next attempt
                    current_attempt += 1
                else:
                    # Either DEFAULT_TO_P4 or reached max attempts
                    if current_attempt >= self.min_attempts:
                        # We've done enough attempts, default to p4
                        final_recommendation = "p4"
                        self.logger.info(
                            f"Defaulting to p4 after {current_attempt} attempts"
                        )
                        break
                    else:
                        # We need to do more attempts
                        current_attempt += 1

            # Default to p4 if we reached max attempts without a recommendation
            if final_recommendation is None:
                final_recommendation = "p4"
                self.logger.info(
                    f"Defaulting to p4 after reaching max attempts: {self.max_attempts}"
                )

            return {
                "recommendation": final_recommendation,
                "attempts": attempts,
                "total_attempts": current_attempt,
            }
        except Exception as e:
            self.logger.error(f"Error processing solver attempts: {e}")
            return {
                "error": str(e),
                "recommendation": "p4",  # Default to p4 on error
                "total_attempts": 0,
            }

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
            import threading

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

                if new_proposals:
                    self.logger.info(
                        f"Found {len(new_proposals)} new proposals to process"
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

    def save_result(self, result):
        """
        Save the result to a file with standardized structure.
        Ensures critical fields are available at both top level and in proposal_metadata.

        Args:
            result: The result dictionary to save

        Returns:
            Path to the saved file or None if saving failed
        """
        if not self.output_dir:
            self.logger.warning("No output directory specified, skipping save")
            return None

        # Create the output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True)

        # Make a copy of the result to avoid modifying the original
        result_copy = result.copy()

        try:
            # Ensure critical fields from proposal_metadata are also at the top level
            top_level_fields = ["tags", "icon", "end_date_iso", "game_start_time"]

            # Handle both single objects and arrays of objects
            if "proposal_metadata" in result_copy and isinstance(
                result_copy["proposal_metadata"], dict
            ):
                metadata = result_copy["proposal_metadata"]
                self.logger.debug(
                    f"Extracting fields from proposal_metadata: {', '.join(top_level_fields)}"
                )

                for field in top_level_fields:
                    # Check if the field exists in the proposal_metadata and not already at the top level
                    if field in metadata and field not in result_copy:
                        result_copy[field] = metadata[field]
                        self.logger.debug(f"Moved field '{field}' to top level")

            # Generate output filename with timestamp
            if "short_id" not in result_copy or not result_copy["short_id"]:
                # Fallback if short_id is missing
                self.logger.warning(
                    "Missing short_id in result, using timestamp only for filename"
                )
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"result_unknown_{timestamp}.json"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"result_{result_copy['short_id']}_{timestamp}.json"

            output_file = self.output_dir / output_filename

            with open(output_file, "w") as f:
                json.dump(result_copy, f, indent=2)

            self.logger.debug(f"Successfully saved full result to {output_file}")
            return output_file

        except (TypeError, KeyError, AttributeError) as e:
            self.logger.error(f"Error processing or saving result: {str(e)}")

            # Try to save with minimal content if there was an error
            try:
                # Create a minimal result with safe getters to avoid exceptions
                minimal_result = {
                    "error": f"Error saving full result: {str(e)}",
                    "timestamp": time.time(),
                    "recommendation": (
                        result.get("recommendation", "p4")
                        if isinstance(result, dict)
                        else "p4"
                    ),
                }

                # Add other fields if they exist
                for field in ["query_id", "short_id", "file_path", "total_attempts"]:
                    if isinstance(result, dict) and field in result:
                        minimal_result[field] = result[field]

                # In case of missing short_id, generate a minimal filename
                if "short_id" not in minimal_result or not minimal_result["short_id"]:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_filename = f"minimal_result_{timestamp}.json"
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_filename = (
                        f"minimal_result_{minimal_result['short_id']}_{timestamp}.json"
                    )

                output_file = self.output_dir / output_filename

                with open(output_file, "w") as f:
                    json.dump(minimal_result, f, indent=2)

                self.logger.warning(
                    f"Saved minimal result to {output_file} after error"
                )
                return output_file

            except Exception as e2:
                self.logger.error(f"Failed to save even minimal result: {str(e2)}")
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
        default=3,
        help="Maximum number of attempts to process a proposal",
    )
    parser.add_argument(
        "--min-attempts",
        type=int,
        default=2,
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

    args = parser.parse_args()

    print(f"🤖 UMA Multi-Operator Proposal Processor 🤖")
    print(f"Monitoring directory: {args.proposals_dir}")

    processor = MultiOperatorProcessor(
        proposals_dir=args.proposals_dir,
        output_dir=args.output_dir,
        max_attempts=args.max_attempts,
        min_attempts=args.min_attempts,
        start_block_number=args.start_block,
        poll_interval=args.poll_interval,
        verbose=args.verbose,
    )

    processor.run()


if __name__ == "__main__":
    main()
