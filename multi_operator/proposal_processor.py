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
from .solvers.code_runner import CodeRunnerSolver
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
            ),
            "code_runner": CodeRunnerSolver(
                api_key=self.openai_api_key, verbose=self.verbose
            ),
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
                tokens = proposal_obj["tokens"]
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

                        if verdict == "SATISFIED":
                            # Overseer is satisfied with the result
                            final_solver_result = current_solver_result
                            break
                        elif (
                            verdict == "RETRY"
                            and require_rerun
                            and current_attempt < max_attempts
                        ):
                            # Update the system prompt if the overseer provided additional guidance
                            prompt_update = overseer_decision.get("prompt_update", "")
                            if prompt_update:
                                updated_system_prompt = f"{updated_system_prompt}\n\nADDITIONAL INSTRUCTIONS: {prompt_update}"
                                self.logger.info(
                                    f"Updated system prompt for {solver_name} retry"
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

                final_result = {
                    "query_id": query_id,
                    "short_id": short_id,
                    "user_prompt": user_prompt,
                    "system_prompt": system_prompt,
                    "router_result": route_result,
                    "solver_results": solver_results,
                    "all_solver_results": all_solver_results,
                    "overseer_result": overseer_result,
                    "recommendation": overseer_decision.get(
                        "verdict", combined_recommendation
                    ),
                    "reason": overseer_decision.get(
                        "reason", "Evaluated by overseer from multiple solver results"
                    ),
                    "market_alignment": overseer_decision.get(
                        "market_alignment", "No market alignment information provided"
                    ),
                    "routing_attempts": current_routing_attempt,
                    "attempted_solvers": attempted_solvers,
                    "rerouting_info": (
                        {
                            "excluded_solvers": excluded_solvers,
                            "overseer_guidance": overseer_guidance,
                        }
                        if current_routing_attempt > 1
                        else None
                    ),
                }
            else:
                # Just use the single solver result as before
                solver_result = solver_results[0] if solver_results else None
                if not solver_result:
                    self.logger.error(f"No solver result for proposal: {short_id}")
                    return None

                # Construct the final result
                overseer_result = solver_result.get("overseer_result", {})
                overseer_decision = overseer_result.get("decision", {})

                final_result = {
                    "query_id": query_id,
                    "short_id": short_id,
                    "user_prompt": user_prompt,
                    "system_prompt": system_prompt,
                    "router_result": route_result,
                    "solver_results": solver_results,
                    "all_solver_results": all_solver_results,
                    "overseer_result": overseer_result,
                    "recommendation": overseer_decision.get(
                        "verdict", solver_result.get("recommendation", "p4")
                    ),
                    "reason": overseer_decision.get("reason", "Evaluated by overseer"),
                    "market_alignment": overseer_decision.get(
                        "market_alignment", "No market alignment information provided"
                    ),
                    "routing_attempts": current_routing_attempt,
                    "attempted_solvers": attempted_solvers,
                    "rerouting_info": (
                        {
                            "excluded_solvers": excluded_solvers,
                            "overseer_guidance": overseer_guidance,
                        }
                        if current_routing_attempt > 1
                        else None
                    ),
                }

            # Save the result
            if self.save_output:
                self.save_result(final_result)

            return final_result

        except Exception as e:
            import traceback

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
