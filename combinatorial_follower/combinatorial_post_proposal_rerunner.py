#!/usr/bin/env python3
"""
Combinatorial Post Proposal Re-runner

This script processes proposals from the proposals directory, queries Perplexity for initial responses,
then uses ChatGPT as an overseer to evaluate and potentially create follow-up prompts for Perplexity.
It supports up to 3 iterations of follow-up prompts to improve the quality of responses.

Usage: python combinatorial_follower/combinatorial_post_proposal_rerunner.py [--proposals_dir PATH] [--output_dir PATH] [--max_concurrent N]
"""

import os
import sys
import json
import time
import threading
import argparse
import concurrent.futures
from pathlib import Path
from datetime import datetime
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import only what we need from common to avoid web3 dependency issues

from common import (
    setup_logging,
    query_perplexity,
    extract_recommendation,
    spinner_animation,
)


from prompt import get_system_prompt

# Load environment variables
load_dotenv()
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
CHATGPT_API_KEY = os.getenv("OPENAI_API_KEY")

# Set up logging
logger = setup_logging("combinatorial_rerunner", "logs/combinatorial_rerunner.log")


class MultiLineSpinner:
    """Spinner that can display status for multiple processes on different lines."""

    def __init__(self, max_lines=10):
        self.max_lines = max_lines
        self.active_spinners = {}
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        self.line_map = {}  # Maps process_id to line number
        self.next_line = 0
        self.error_count = 0

    def start(self):
        """Start the spinner thread."""
        if self.running:
            return

        try:
            self.running = True
            self.thread = threading.Thread(target=self._spin, daemon=True)
            self.thread.start()

            # Print empty lines to make space for spinners
            for _ in range(self.max_lines):
                print()
            # Move cursor back up
            print(f"\033[{self.max_lines}A", end="", flush=True)
        except Exception as e:
            logger.error(f"Error starting spinner: {e}", exc_info=True)
            self.running = False

    def stop(self):
        """Stop the spinner thread."""
        try:
            self.running = False
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=1.0)  # Wait up to 1 second

            # Clear all spinner lines
            with self.lock:
                for line in range(self.max_lines):
                    # Move to line, clear it, and reset cursor
                    print(f"\033[{line+1};1H\033[K", end="", flush=True)

                # Move cursor to the bottom
                print(f"\033[{self.max_lines}B", end="", flush=True)
            logger.info("Spinner stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping spinner: {e}", exc_info=True)

    def add_spinner(self, process_id, text):
        """Add a new spinner for a process."""
        try:
            with self.lock:
                if self.next_line >= self.max_lines:
                    # Reuse lines if we exceed max
                    self.next_line = 0

                self.line_map[process_id] = self.next_line
                self.active_spinners[process_id] = {
                    "text": text,
                    "index": 0,
                    "start_time": time.time(),
                }
                self.next_line += 1

                if not self.running:
                    self.start()
                logger.debug(f"Added spinner for {process_id}: {text}")
        except Exception as e:
            logger.error(f"Error adding spinner for {process_id}: {e}", exc_info=True)

    def update_spinner(self, process_id, text):
        """Update the text for an existing spinner."""
        try:
            with self.lock:
                if process_id in self.active_spinners:
                    self.active_spinners[process_id]["text"] = text
                    logger.debug(f"Updated spinner for {process_id}: {text}")
        except Exception as e:
            logger.error(f"Error updating spinner for {process_id}: {e}", exc_info=True)

    def remove_spinner(self, process_id):
        """Remove a spinner."""
        try:
            # Use a timeout to prevent potential deadlocks
            lock_acquired = False
            try:
                # Try to acquire the lock with a timeout to prevent deadlocks
                lock_acquired = self.lock.acquire(timeout=2.0)  # 2-second timeout

                if not lock_acquired:
                    logger.error(
                        f"Timed out acquiring lock to remove spinner for {process_id}"
                    )
                    return

                if process_id in self.active_spinners:
                    line = self.line_map[process_id]
                    # Clear the line
                    print(f"\033[{line+1};1H\033[K", end="", flush=True)
                    del self.active_spinners[process_id]
                    del self.line_map[process_id]
                    logger.debug(f"Removed spinner for {process_id}")

                    if not self.active_spinners:
                        logger.info("No active spinners left, stopping spinner thread")
                        self.stop()
            finally:
                # Always release the lock if we acquired it
                if lock_acquired:
                    self.lock.release()
        except Exception as e:
            logger.error(f"Error removing spinner for {process_id}: {e}", exc_info=True)

    def _spin(self):
        """Spinner animation loop."""
        try:
            while self.running and self.active_spinners:
                try:
                    with self.lock:
                        for process_id, spinner in self.active_spinners.items():
                            try:
                                line = self.line_map[process_id]
                                char = self.spinner_chars[
                                    spinner["index"] % len(self.spinner_chars)
                                ]
                                elapsed = time.time() - spinner["start_time"]

                                # Move to the correct line, clear it, and print the spinner
                                print(
                                    f"\033[{line+1};1H\033[K{char} {spinner['text']} ({elapsed:.1f}s)",
                                    end="",
                                    flush=True,
                                )

                                # Update spinner index
                                spinner["index"] += 1
                            except Exception as e:
                                # Log error but continue with other spinners
                                self.error_count += 1
                                if (
                                    self.error_count <= 5
                                ):  # Limit error logging to avoid flooding
                                    logger.error(
                                        f"Error updating spinner display for {process_id}: {e}"
                                    )
                except Exception as e:
                    logger.error(f"Error in spinner loop: {e}", exc_info=True)

                time.sleep(0.1)
        except Exception as e:
            logger.error(f"Fatal error in spinner thread: {e}", exc_info=True)
            self.running = False


# Create a global spinner manager
spinner_manager = MultiLineSpinner(max_lines=20)


class RateLimiter:
    """Rate limiter for API calls with a maximum of N requests per minute."""

    def __init__(self, name, max_requests_per_minute=5):
        self.name = name
        self.max_requests = max_requests_per_minute
        self.request_timestamps = deque(maxlen=max_requests_per_minute)
        self.lock = threading.Lock()
        self.in_flight = 0
        self.in_flight_lock = threading.Lock()
        logger.info(
            f"[DEBUG] Initialized {self.name} RateLimiter with max {max_requests_per_minute} requests per minute"
        )

    def wait_if_needed(self):
        """Wait if needed to comply with rate limits. Returns wait time in seconds."""
        logger.info(
            f"[DEBUG] {self.name} RateLimiter.wait_if_needed entered at {datetime.now().strftime('%H:%M:%S.%f')}"
        )
        with self.lock:
            now = time.time()
            logger.info(
                f"[DEBUG] {self.name} RateLimiter: Current queue has {len(self.request_timestamps)} timestamps"
            )

            # If we haven't made enough requests yet, no need to wait
            if len(self.request_timestamps) < self.max_requests:
                self.request_timestamps.append(now)
                logger.info(
                    f"[DEBUG] {self.name} RateLimiter: Queue not full, no waiting needed"
                )
                return 0

            # Check if the oldest request is more than 60 seconds old
            oldest_request_time = self.request_timestamps[0]
            time_since_oldest = now - oldest_request_time
            logger.info(
                f"[DEBUG] {self.name} RateLimiter: Oldest request was {time_since_oldest:.2f} seconds ago"
            )

            if time_since_oldest < 60:
                # Need to wait until the oldest request is 60 seconds old
                wait_time = 60 - time_since_oldest
                logger.info(
                    f"[DEBUG] {self.name} rate limit reached. Waiting {wait_time:.2f} seconds before next request"
                )
                time.sleep(wait_time)
                now = time.time()  # Update time after waiting
            else:
                wait_time = 0
                logger.info(
                    f"[DEBUG] {self.name} RateLimiter: No waiting needed (oldest request is old enough)"
                )

            # Remove the oldest timestamp and add the new one
            logger.info(
                f"[DEBUG] {self.name} RateLimiter: Removing oldest timestamp and adding new one"
            )
            self.request_timestamps.popleft()
            self.request_timestamps.append(now)

            logger.info(
                f"[DEBUG] {self.name} RateLimiter.wait_if_needed exiting at {datetime.now().strftime('%H:%M:%S.%f')}"
            )
            return max(0, 60 - time_since_oldest)

    def increment_in_flight(self):
        """Increment the count of in-flight requests."""
        with self.in_flight_lock:
            self.in_flight += 1
            logger.info(
                f"[DEBUG] {self.name} RateLimiter: Incremented in-flight to {self.in_flight}"
            )
            return self.in_flight

    def decrement_in_flight(self):
        """Decrement the count of in-flight requests."""
        try:
            # Try to acquire the lock with a timeout to prevent deadlocks
            if self.in_flight_lock.acquire(timeout=2.0):  # 2-second timeout
                try:
                    self.in_flight -= 1
                    logger.info(
                        f"[DEBUG] {self.name} RateLimiter: Decremented in-flight to {self.in_flight}"
                    )
                    return self.in_flight
                finally:
                    self.in_flight_lock.release()
            else:
                logger.error(
                    f"[DEBUG] {self.name} RateLimiter: Timed out acquiring lock for decrement_in_flight"
                )
                return None
        except Exception as e:
            logger.error(
                f"[DEBUG] {self.name} RateLimiter: Error in decrement_in_flight: {e}"
            )
            return None

    def get_in_flight(self):
        """Get the current number of in-flight requests."""
        with self.in_flight_lock:
            return self.in_flight


# Create global rate limiter instances
perplexity_rate_limiter = RateLimiter("Perplexity", max_requests_per_minute=5)
chatgpt_rate_limiter = RateLimiter("ChatGPT", max_requests_per_minute=10)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Combinatorial Post Proposal Re-runner"
    )
    parser.add_argument(
        "--proposals_dir",
        type=str,
        default="proposal_replayer/proposals",
        help="Directory containing proposal files",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="combinatorial_follower/results",
        help="Directory to save outputs",
    )
    parser.add_argument(
        "--max_concurrent",
        type=int,
        default=5,
        help="Maximum number of concurrent proposal processings",
    )
    parser.add_argument(
        "--max_iterations",
        type=int,
        default=3,
        help="Maximum number of follow-up iterations (0-3)",
    )
    parser.add_argument(
        "--sample_size",
        type=int,
        default=0,
        help="Number of samples to process (0 for all)",
    )
    parser.add_argument(
        "--disable_spinner",
        action="store_true",
        help="Disable the spinner UI (use if you experience display issues)",
    )
    parser.add_argument(
        "--perplexity_only",
        action="store_true",
        help="Only get responses from Perplexity, skip ChatGPT evaluation",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Timeout in seconds (default: 900 seconds = 15 minutes)",
    )
    return parser.parse_args()


def format_prompt_from_json(proposal_data):
    """Format user prompt from proposal data."""
    if isinstance(proposal_data, list) and len(proposal_data) > 0:
        proposal_data = proposal_data[0]

    ancillary_data = proposal_data.get("ancillary_data", "")
    resolution_conditions = proposal_data.get("resolution_conditions", "")
    updates = proposal_data.get("updates", [])

    prompt = f"\n\nancillary_data:\n{ancillary_data}\n\n"
    if resolution_conditions:
        prompt += f"resolution_conditions:\n{resolution_conditions}\n\n"
    if updates:
        prompt += f"updates:\n{updates}\n\n"
    return prompt


def get_query_id_from_proposal(proposal_data):
    """Extract the query ID from proposal data."""
    if isinstance(proposal_data, list) and len(proposal_data) > 0:
        return proposal_data[0].get("query_id", "")
    return proposal_data.get("query_id", "")


def get_question_id_short(query_id):
    """Get a shortened version of the query ID."""
    if not query_id:
        return "unknown"
    return query_id[2:10] if query_id.startswith("0x") else query_id[:8]


def get_output_filename(question_id_short):
    """Generate the output filename based on question ID."""
    return f"{question_id_short}.json"


def is_already_processed(question_id_short, output_dir):
    """Check if a proposal has already been processed."""
    return (Path(output_dir) / get_output_filename(question_id_short)).exists()


def query_chatgpt(prompt, api_key):
    """Query ChatGPT with a prompt."""
    debug_start = time.time()
    logger.info(
        f"[DEBUG] query_chatgpt START at {datetime.fromtimestamp(debug_start).strftime('%H:%M:%S.%f')}"
    )
    try:
        logger.info(
            f"[DEBUG] Step 1: Checking rate limits at {datetime.now().strftime('%H:%M:%S.%f')}"
        )
        # Wait if needed to respect rate limits
        wait_time = chatgpt_rate_limiter.wait_if_needed()
        logger.info(f"[DEBUG] Rate limit wait time was {wait_time} seconds")

        in_flight = chatgpt_rate_limiter.increment_in_flight()
        logger.info(f"[DEBUG] Current in-flight ChatGPT requests: {in_flight}")

        logger.info(
            f"[DEBUG] Step 2: Importing OpenAI at {datetime.now().strftime('%H:%M:%S.%f')}"
        )
        from openai import OpenAI

        try:
            logger.info(
                f"[DEBUG] Step 3: Creating OpenAI client at {datetime.now().strftime('%H:%M:%S.%f')}"
            )
            client = OpenAI(api_key=api_key)

            logger.info(
                f"[DEBUG] Step 4: Making API call at {datetime.now().strftime('%H:%M:%S.%f')}"
            )
            logger.info(f"[DEBUG] Prompt length: {len(prompt)} characters")

            response_start = time.time()
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                timeout=60,  # 60-second timeout
            )
            response_time = time.time() - response_start

            logger.info(
                f"[DEBUG] Step 5: API call completed in {response_time:.2f}s at {datetime.now().strftime('%H:%M:%S.%f')}"
            )

            if not hasattr(response, "choices") or len(response.choices) == 0:
                logger.error("[DEBUG] Response has no choices!")
                return None

            if not hasattr(response.choices[0], "message") or not hasattr(
                response.choices[0].message, "content"
            ):
                logger.error("[DEBUG] Response has invalid message structure!")
                return None

            content = response.choices[0].message.content
            logger.info(f"[DEBUG] Response content length: {len(content)} characters")
            return content

        except ImportError as e:
            logger.error(
                f"[DEBUG] Failed to import OpenAI at {datetime.now().strftime('%H:%M:%S.%f')}: {e}"
            )
            return None
        except Exception as e:
            logger.error(
                f"[DEBUG] Error during ChatGPT API call at {datetime.now().strftime('%H:%M:%S.%f')}: {e}"
            )
            return None
    except Exception as e:
        logger.error(
            f"[DEBUG] Unexpected error in query_chatgpt at {datetime.now().strftime('%H:%M:%S.%f')}: {e}",
            exc_info=True,
        )
        return None
    finally:
        chatgpt_rate_limiter.decrement_in_flight()
        debug_end = time.time()
        logger.info(
            f"[DEBUG] query_chatgpt END at {datetime.fromtimestamp(debug_end).strftime('%H:%M:%S.%f')}, total duration: {debug_end - debug_start:.2f}s"
        )


def parse_chatgpt_response(response: str) -> Tuple[bool, Optional[str]]:
    """
    Parse the ChatGPT response to determine satisfaction and follow-up prompt.

    Returns:
        Tuple[bool, Optional[str]]: (is_satisfied, follow_up_prompt)
    """
    if not response:
        return False, None

    # Extract satisfaction (YES/NO)
    satisfaction_line = None
    for line in response.split("\n"):
        if line.startswith("SATISFACTION:"):
            satisfaction_line = line.replace("SATISFACTION:", "").strip()
            break

    is_satisfied = satisfaction_line and satisfaction_line.upper() == "YES"

    # Extract follow-up prompt if not satisfied
    follow_up_prompt = None
    if not is_satisfied:
        in_follow_up = False
        follow_up_lines = []

        for line in response.split("\n"):
            if line.startswith("FOLLOW-UP PROMPT"):
                in_follow_up = True
                continue
            if in_follow_up:
                follow_up_lines.append(line)

        if follow_up_lines:
            follow_up_prompt = "\n".join(follow_up_lines).strip()

    return is_satisfied, follow_up_prompt


def create_chatgpt_evaluation_prompt(user_prompt, system_prompt, perplexity_response):
    """Create a prompt for ChatGPT to evaluate Perplexity's response."""
    prompt = f"""
You are acting as an Overseer for AI responses. Your task is to evaluate responses from Perplexity AI and determine if they are satisfactory or need improvement.

ORIGINAL USER PROMPT:
{user_prompt}

SYSTEM PROMPT:
{system_prompt}

PERPLEXITY RESPONSE:
{perplexity_response}

Your job is to:
1. Analyze if Perplexity's response appropriately addresses the query
2. Determine if the response is accurate, complete, and follows the guidelines in the system prompt
3. If you are NOT satisfied with the response, create a follow-up prompt for Perplexity

Your output format should be:

REVIEW:
[Your detailed review of Perplexity's response, highlighting strengths and weaknesses]

SATISFACTION:
[YES/NO] - Indicate if you are satisfied with the response

REASONING:
[Explain your reasoning for being satisfied or not]

FOLLOW-UP PROMPT (if not satisfied):
[Write a follow-up prompt for Perplexity that addresses the issues in the initial response]
"""
    return prompt


def create_chatgpt_follow_up_evaluation_prompt(
    original_user_prompt,
    system_prompt,
    original_response,
    follow_up_prompt,
    new_response,
):
    """Create a prompt for ChatGPT to evaluate Perplexity's follow-up response."""
    prompt = f"""
You are acting as an Overseer for AI responses. Your task is to evaluate responses from Perplexity AI and determine if they are satisfactory or need improvement.

ORIGINAL USER PROMPT:
{original_user_prompt}

SYSTEM PROMPT:
{system_prompt}

PREVIOUS PERPLEXITY RESPONSE:
{original_response}

FOLLOW-UP PROMPT:
{follow_up_prompt}

NEW PERPLEXITY RESPONSE:
{new_response}

Your job is to:
1. Analyze if the new response satisfactorily addresses the issues in the previous response
2. Determine if the response is accurate, complete, and follows the guidelines in the system prompt
3. If you are still NOT satisfied, create another follow-up prompt for Perplexity

Your output format should be:

REVIEW:
[Your detailed review of the new response, highlighting improvements and remaining issues]

SATISFACTION:
[YES/NO] - Indicate if you are now satisfied with the response

REASONING:
[Explain your reasoning for being satisfied or not]

FOLLOW-UP PROMPT (if not satisfied):
[Write another follow-up prompt for Perplexity that addresses the remaining issues]
"""
    return prompt


def run_iterative_prompting(
    question_id_short, user_prompt, system_prompt, max_iterations=3
):
    """
    Run the iterative prompting process for a proposal.

    Args:
        question_id_short: Shortened question ID
        user_prompt: The original user prompt
        system_prompt: The system prompt for Perplexity
        max_iterations: Maximum number of iterations

    Returns:
        Dict: Results of the iterative prompting process
    """
    logger.info(f"[{question_id_short}] STARTED run_iterative_prompting function")
    print(f"DEBUG-ITER-1: Starting run_iterative_prompting for {question_id_short}")

    # Initialize results dictionary
    results = {
        "question_id_short": question_id_short,
        "original_user_prompt": user_prompt,
        "system_prompt": system_prompt,
        "iterations": [],
        "timestamp": time.time(),
        "total_iterations": 0,
        "final_recommendation": None,
    }

    # Check if ChatGPT API key is valid
    if not CHATGPT_API_KEY or len(CHATGPT_API_KEY.strip()) < 10:
        logger.error(f"[{question_id_short}] Invalid or missing ChatGPT API key")
        results["error"] = "Invalid or missing ChatGPT API key"
        return results

    logger.info(f"[{question_id_short}] Starting iteration 0 (initial query)")
    print(f"DEBUG-ITER-2: Starting Perplexity query for {question_id_short}")

    # === INITIAL PERPLEXITY QUERY (ITERATION 0) ===

    # Setup iteration result
    iteration_result = {
        "iteration": 0,
        "user_prompt": user_prompt,
    }

    # Add spinner for Perplexity
    perplexity_process_id = f"{question_id_short}-perplexity-0"
    try:
        spinner_manager.add_spinner(
            perplexity_process_id,
            f"[{question_id_short}] Querying Perplexity (initial query)",
        )
    except Exception as e:
        logger.error(
            f"[{question_id_short}] Error adding Perplexity spinner: {e}", exc_info=True
        )

    try:
        # Wait for rate limits
        logger.info(f"[{question_id_short}] Checking Perplexity rate limits")
        perplexity_rate_limiter.wait_if_needed()
        perplexity_rate_limiter.increment_in_flight()

        # Query Perplexity
        logger.info(f"[{question_id_short}] Sending initial Perplexity query")
        perplexity_start_time = time.time()
        perplexity_response = query_perplexity(
            user_prompt, PERPLEXITY_API_KEY, verbose=False
        )
        perplexity_time = time.time() - perplexity_start_time
        logger.info(
            f"[{question_id_short}] Received Perplexity response in {perplexity_time:.2f}s"
        )
        print(f"DEBUG-ITER-3: Received Perplexity response for {question_id_short}")

        # Decrement in-flight counter early to avoid deadlocks
        try:
            perplexity_rate_limiter.decrement_in_flight()
            print(
                f"DEBUG-ITER-3.1: Decremented in-flight counter for {question_id_short}"
            )
        except Exception as e:
            logger.error(
                f"[{question_id_short}] Error decrementing in-flight counter: {e}",
                exc_info=True,
            )
            print(
                f"DEBUG-ITER-ERROR-DECREMENT: Error decrementing counter for {question_id_short}: {e}"
            )

        # Process Perplexity response
        response_text = perplexity_response.choices[0].message.content
        citations = (
            [citation for citation in perplexity_response.citations]
            if hasattr(perplexity_response, "citations")
            else []
        )

        # Extract recommendation
        recommendation = extract_recommendation(response_text)
        logger.info(f"[{question_id_short}] Extracted recommendation: {recommendation}")
        print(
            f"DEBUG-ITER-4: Extracted recommendation for {question_id_short}: {recommendation}"
        )

        # Record Perplexity response
        iteration_result["perplexity_response"] = {
            "response": response_text,
            "recommendation": recommendation,
            "citations": citations,
            "api_time_seconds": perplexity_time,
            "model": perplexity_response.model,
            "token_usage": {
                "completion_tokens": perplexity_response.usage.completion_tokens,
                "prompt_tokens": perplexity_response.usage.prompt_tokens,
                "total_tokens": perplexity_response.usage.total_tokens,
            },
        }

        # Update results with initial data
        results["iterations"].append(iteration_result)
        results["final_recommendation"] = recommendation
        results["total_iterations"] = 1

        logger.info(f"[{question_id_short}] Successfully processed Perplexity response")
        print(
            f"DEBUG-ITER-5: Successfully processed Perplexity response for {question_id_short}"
        )

    except Exception as e:
        logger.error(
            f"[{question_id_short}] Error during Perplexity query: {e}", exc_info=True
        )
        print(
            f"DEBUG-ITER-ERROR-1: Error during Perplexity query for {question_id_short}: {e}"
        )
        iteration_result["perplexity_error"] = str(e)
        results["iterations"].append(iteration_result)
        results["error"] = f"Perplexity query error: {e}"
        return results
    finally:
        # Remove spinner - don't decrement here since we did it earlier
        try:
            spinner_manager.remove_spinner(perplexity_process_id)
            print(f"DEBUG-ITER-6: Removed spinner for {question_id_short}")
        except Exception as e:
            logger.error(
                f"[{question_id_short}] Error removing Perplexity spinner: {e}",
                exc_info=True,
            )
            print(
                f"DEBUG-ITER-ERROR-SPINNER: Error removing spinner for {question_id_short}: {e}"
            )
        print(f"DEBUG-ITER-6: Cleaned up Perplexity resources for {question_id_short}")

    # If iterations are disabled, return after initial query
    if max_iterations <= 0:
        logger.info(
            f"[{question_id_short}] Max iterations set to 0, skipping ChatGPT evaluation"
        )
        logger.info(f"[{question_id_short}] COMPLETED run_iterative_prompting function")
        print(
            f"DEBUG-ITER-7: COMPLETED run_iterative_prompting with no iterations for {question_id_short}"
        )
        return results

    # === CHATGPT EVALUATION ===
    logger.info(
        f"[{question_id_short}] Starting ChatGPT evaluation at {datetime.now().strftime('%H:%M:%S.%f')}"
    )

    # Create ChatGPT evaluation prompt
    logger.info(
        f"[DEBUG] [{question_id_short}] Creating evaluation prompt at {datetime.now().strftime('%H:%M:%S.%f')}"
    )
    chatgpt_prompt = create_chatgpt_evaluation_prompt(
        user_prompt, system_prompt, response_text
    )
    logger.info(
        f"[DEBUG] [{question_id_short}] Created prompt of length {len(chatgpt_prompt)} at {datetime.now().strftime('%H:%M:%S.%f')}"
    )

    # Add spinner for ChatGPT
    chatgpt_process_id = f"{question_id_short}-chatgpt-0"
    try:
        logger.info(
            f"[DEBUG] [{question_id_short}] Adding spinner at {datetime.now().strftime('%H:%M:%S.%f')}"
        )
        spinner_manager.add_spinner(
            chatgpt_process_id,
            f"[{question_id_short}] Evaluating with ChatGPT",
        )
        logger.info(
            f"[DEBUG] [{question_id_short}] Added spinner successfully at {datetime.now().strftime('%H:%M:%S.%f')}"
        )
    except Exception as e:
        logger.error(
            f"[{question_id_short}] Error adding ChatGPT spinner at {datetime.now().strftime('%H:%M:%S.%f')}: {e}",
            exc_info=True,
        )

    try:
        # Direct query to ChatGPT with manual timeout
        logger.info(
            f"[{question_id_short}] Preparing ChatGPT query at {datetime.now().strftime('%H:%M:%S.%f')}"
        )
        chatgpt_start_time = time.time()

        # Simple timeout mechanism
        import threading

        chatgpt_response = [None]  # Use list to store result from thread
        chatgpt_error = [None]
        thread_started = [False]
        thread_completed = [False]

        def query_with_timeout():
            try:
                thread_started[0] = True
                logger.info(
                    f"[{question_id_short}] ChatGPT query thread started at {datetime.now().strftime('%H:%M:%S.%f')}"
                )
                response = query_chatgpt(chatgpt_prompt, CHATGPT_API_KEY)
                logger.info(
                    f"[{question_id_short}] query_chatgpt returned at {datetime.now().strftime('%H:%M:%S.%f')}"
                )
                chatgpt_response[0] = response
                logger.info(
                    f"[{question_id_short}] Response stored in thread variable at {datetime.now().strftime('%H:%M:%S.%f')}"
                )
                thread_completed[0] = True
            except Exception as e:
                logger.error(
                    f"[{question_id_short}] Error in ChatGPT thread at {datetime.now().strftime('%H:%M:%S.%f')}: {e}",
                    exc_info=True,
                )
                chatgpt_error[0] = str(e)
                thread_completed[0] = True

        # Start thread
        logger.info(
            f"[{question_id_short}] Creating thread at {datetime.now().strftime('%H:%M:%S.%f')}"
        )
        chatgpt_thread = threading.Thread(target=query_with_timeout)
        chatgpt_thread.daemon = True
        logger.info(
            f"[{question_id_short}] Starting thread at {datetime.now().strftime('%H:%M:%S.%f')}"
        )
        chatgpt_thread.start()
        logger.info(
            f"[{question_id_short}] Thread started at {datetime.now().strftime('%H:%M:%S.%f')}"
        )

        # Wait with timeout
        logger.info(
            f"[{question_id_short}] Waiting for ChatGPT response (max 5 minutes) at {datetime.now().strftime('%H:%M:%S.%f')}"
        )
        join_start = time.time()
        chatgpt_thread.join(timeout=300)  # 5 minutes timeout
        join_duration = time.time() - join_start
        logger.info(
            f"[{question_id_short}] Thread join completed after {join_duration:.2f}s at {datetime.now().strftime('%H:%M:%S.%f')}"
        )

        chatgpt_time = time.time() - chatgpt_start_time
        logger.info(
            f"[{question_id_short}] ChatGPT processing time: {chatgpt_time:.2f}s at {datetime.now().strftime('%H:%M:%S.%f')}"
        )
        logger.info(
            f"[DEBUG] [{question_id_short}] Thread started: {thread_started[0]}"
        )
        logger.info(
            f"[DEBUG] [{question_id_short}] Thread completed: {thread_completed[0]}"
        )

        # Check if thread is still alive (timed out)
        if chatgpt_thread.is_alive():
            logger.error(
                f"[{question_id_short}] ChatGPT query timed out after 5 minutes at {datetime.now().strftime('%H:%M:%S.%f')}"
            )
            # Thread is still running but we're moving on
            iteration_result["chatgpt_evaluation"] = {
                "prompt": chatgpt_prompt,
                "response": "Error: ChatGPT query timed out",
                "is_satisfied": "true",  # Force satisfaction to end iterations
                "follow_up_prompt": None,
                "api_time_seconds": chatgpt_time,
                "error": "Timeout",
            }
            logger.info(
                f"[{question_id_short}] Created timeout evaluation result at {datetime.now().strftime('%H:%M:%S.%f')}"
            )
        elif chatgpt_error[0]:
            # Thread encountered an exception
            logger.error(
                f"[{question_id_short}] ChatGPT query failed with error: {chatgpt_error[0]} at {datetime.now().strftime('%H:%M:%S.%f')}"
            )
            iteration_result["chatgpt_evaluation"] = {
                "prompt": chatgpt_prompt,
                "response": f"Error: {chatgpt_error[0]}",
                "is_satisfied": "true",  # Force satisfaction to end iterations
                "follow_up_prompt": None,
                "api_time_seconds": chatgpt_time,
                "error": chatgpt_error[0],
            }
            logger.info(
                f"[{question_id_short}] Created error evaluation result at {datetime.now().strftime('%H:%M:%S.%f')}"
            )
        elif chatgpt_response[0] is None:
            # Thread completed but returned None
            logger.error(
                f"[{question_id_short}] ChatGPT returned None at {datetime.now().strftime('%H:%M:%S.%f')}"
            )
            iteration_result["chatgpt_evaluation"] = {
                "prompt": chatgpt_prompt,
                "response": "Error: ChatGPT returned None",
                "is_satisfied": "true",  # Force satisfaction to end iterations
                "follow_up_prompt": None,
                "api_time_seconds": chatgpt_time,
                "error": "Null response",
            }
            logger.info(
                f"[{question_id_short}] Created null response evaluation result at {datetime.now().strftime('%H:%M:%S.%f')}"
            )
        else:
            # Thread completed successfully
            logger.info(
                f"[{question_id_short}] Parsing ChatGPT response at {datetime.now().strftime('%H:%M:%S.%f')}"
            )
            is_satisfied, follow_up_prompt = parse_chatgpt_response(chatgpt_response[0])
            logger.info(
                f"[{question_id_short}] Parsed ChatGPT response at {datetime.now().strftime('%H:%M:%S.%f')}"
            )

            iteration_result["chatgpt_evaluation"] = {
                "prompt": chatgpt_prompt,
                "response": chatgpt_response[0],
                "is_satisfied": str(is_satisfied).lower(),
                "follow_up_prompt": follow_up_prompt,
                "api_time_seconds": chatgpt_time,
            }
            logger.info(
                f"[{question_id_short}] Created successful evaluation result at {datetime.now().strftime('%H:%M:%S.%f')}"
            )

            logger.info(
                f"[{question_id_short}] ChatGPT satisfaction: {is_satisfied} at {datetime.now().strftime('%H:%M:%S.%f')}"
            )

            # If ChatGPT is not satisfied and provided a follow-up, we would do another iteration
            # But for simplicity, we're stopping at one iteration for now
            if not is_satisfied and follow_up_prompt:
                logger.info(
                    f"[{question_id_short}] ChatGPT suggested follow-up, but limiting to 1 iteration for simplicity at {datetime.now().strftime('%H:%M:%S.%f')}"
                )

        # Update results
        logger.info(
            f"[{question_id_short}] Updating results with evaluation at {datetime.now().strftime('%H:%M:%S.%f')}"
        )
        results["iterations"][0] = iteration_result  # Update the existing iteration
        logger.info(
            f"[{question_id_short}] Updated results successfully at {datetime.now().strftime('%H:%M:%S.%f')}"
        )

    except Exception as e:
        logger.error(
            f"[{question_id_short}] Error in ChatGPT evaluation: {e} at {datetime.now().strftime('%H:%M:%S.%f')}",
            exc_info=True,
        )
        iteration_result["chatgpt_error"] = str(e)
        results["error"] = f"ChatGPT evaluation error: {e}"
        logger.info(
            f"[{question_id_short}] Recorded error in results at {datetime.now().strftime('%H:%M:%S.%f')}"
        )
    finally:
        # Remove spinner
        try:
            logger.info(
                f"[{question_id_short}] Removing spinner at {datetime.now().strftime('%H:%M:%S.%f')}"
            )
            spinner_manager.remove_spinner(chatgpt_process_id)
            logger.info(
                f"[{question_id_short}] Spinner removed at {datetime.now().strftime('%H:%M:%S.%f')}"
            )
        except Exception as e:
            logger.error(
                f"[{question_id_short}] Error removing ChatGPT spinner: {e} at {datetime.now().strftime('%H:%M:%S.%f')}",
                exc_info=True,
            )

    # Final logging
    logger.info(f"[{question_id_short}] Completed run_iterative_prompting function")
    print(
        f"DEBUG-ITER-FINAL: Completed run_iterative_prompting function for {question_id_short}"
    )
    return results


def process_proposal_file(file_path, output_dir, max_iterations):
    """Process a single proposal file."""
    file_name = os.path.basename(file_path)
    logger.info(f"STARTED processing proposal file: {file_name}")

    try:
        # Create output directory if it doesn't exist
        logger.info(f"Ensuring output directory exists: {output_dir}")
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Load proposal data
        logger.info(f"Loading proposal data from {file_path}")
        with open(file_path, "r") as f:
            proposal_data = json.load(f)

        # Extract query ID
        query_id = get_query_id_from_proposal(proposal_data)
        question_id_short = get_question_id_short(query_id)
        logger.info(f"Extracted question ID: {question_id_short}")

        # Check if already processed
        output_file = Path(output_dir) / get_output_filename(question_id_short)
        if output_file.exists():
            logger.info(f"Proposal {question_id_short} already processed, skipping")
            return True

        # Format prompts
        logger.info(f"Formatting user prompt for {question_id_short}")
        user_prompt = format_prompt_from_json(proposal_data)

        logger.info(f"Getting system prompt")
        system_prompt = get_system_prompt()

        # Extract raw data
        if isinstance(proposal_data, list) and len(proposal_data) > 0:
            raw_data = proposal_data[0]
        else:
            raw_data = proposal_data

        # Run the iterative prompting process - this is the core function
        logger.info(f"Starting iterative prompting for {question_id_short}")
        try:
            results = run_iterative_prompting(
                question_id_short, user_prompt, system_prompt, max_iterations
            )
            logger.info(
                f"Successfully completed iterative prompting for {question_id_short}"
            )
            # DEBUG MARKER 1
            print(
                f"DEBUG MARKER 1: Completed iterative prompting for {question_id_short}"
            )
        except Exception as e:
            logger.error(
                f"Error during iterative prompting for {question_id_short}: {e}",
                exc_info=True,
            )
            # Create minimal results
            logger.info(f"Creating minimal results structure due to error")
            results = {
                "question_id_short": question_id_short,
                "original_user_prompt": user_prompt,
                "system_prompt": system_prompt,
                "iterations": [],
                "total_iterations": 0,
                "timestamp": time.time(),
                "final_recommendation": "None",
                "error": str(e),
            }

        # DEBUG MARKER 2
        print(f"DEBUG MARKER 2: About to create metadata for {question_id_short}")
        # Create basic metadata from the proposal
        logger.info(f"Creating metadata for {question_id_short}")
        proposal_metadata = {
            "creator": raw_data.get("creator", ""),
            "proposal_bond": raw_data.get("proposal_bond", 0),
            "reward_amount": raw_data.get("reward_amount", 0),
            "unix_timestamp": raw_data.get("unix_timestamp", 0),
            "block_number": raw_data.get("block_number", 0),
            "updates": raw_data.get("updates", []),
            "ancillary_data_hex": raw_data.get("ancillary_data_hex", ""),
        }

        # DEBUG MARKER 3
        print(f"DEBUG MARKER 3: About to build final output for {question_id_short}")
        # Build final output structure
        logger.info(f"Building final output for {question_id_short}")
        final_output = {
            "query_id": query_id,
            "question_id_short": question_id_short,
            "transaction_hash": raw_data.get("transaction_hash", ""),
            "user_prompt": user_prompt,
            "system_prompt": system_prompt,
            "processed_file": file_name,
            "proposal_metadata": proposal_metadata,
            "timestamp": results.get("timestamp", time.time()),
            "iterations": results.get("iterations", []),
            "total_iterations": results.get("total_iterations", 0),
            "recommendation": results.get("final_recommendation", "None"),
        }

        # DEBUG MARKER 4
        print(
            f"DEBUG MARKER 4: About to process first iteration data for {question_id_short}"
        )
        # Add the first Perplexity response if available
        first_iteration = None
        if results.get("iterations") and len(results["iterations"]) > 0:
            first_iteration = results["iterations"][0]

        if first_iteration and "perplexity_response" in first_iteration:
            logger.info(f"Adding Perplexity response data for {question_id_short}")
            first_response = first_iteration["perplexity_response"]
            final_output["response"] = first_response.get("response", "")
            final_output["citations"] = first_response.get("citations", [])

            # Add response metadata
            final_output["response_metadata"] = {
                "model": first_response.get("model", ""),
                "created_timestamp": int(final_output["timestamp"]),
                "created_datetime": datetime.fromtimestamp(
                    final_output["timestamp"]
                ).strftime("%Y-%m-%dT%H:%M:%S"),
                "completion_tokens": first_response.get("token_usage", {}).get(
                    "completion_tokens", 0
                ),
                "prompt_tokens": first_response.get("token_usage", {}).get(
                    "prompt_tokens", 0
                ),
                "total_tokens": first_response.get("token_usage", {}).get(
                    "total_tokens", 0
                ),
                "api_response_time_seconds": first_response.get("api_time_seconds", 0),
            }
        else:
            logger.warning(
                f"No Perplexity response data available for {question_id_short}"
            )

        # DEBUG MARKER 5
        print(f"DEBUG MARKER 5: About to add optional fields for {question_id_short}")
        # Add optional fields if present
        if "proposed_price" in raw_data and raw_data["proposed_price"] is not None:
            final_output["proposed_price"] = raw_data["proposed_price"]
            final_output["proposed_price_outcome"] = f"p{raw_data['proposed_price']}"

        if "resolved_price" in raw_data and raw_data["resolved_price"] is not None:
            final_output["resolved_price"] = raw_data["resolved_price"]
            final_output["resolved_price_outcome"] = f"p{raw_data['resolved_price']}"

        # Add tags if they exist
        tags = raw_data.get("tags", [])
        if tags:
            final_output["tags"] = tags

        # Add disputed status if available
        if "disputed" in raw_data:
            final_output["disputed"] = raw_data["disputed"]

        # Add any error information
        if "error" in results:
            final_output["error"] = results["error"]

        # DEBUG MARKER 6
        print(f"DEBUG MARKER 6: About to save results to {output_file}")
        # Save the final output
        logger.info(f"Saving results to {output_file}")
        try:
            # Make sure the output directory exists right before saving
            output_dir_path = Path(output_dir)
            output_dir_path.mkdir(parents=True, exist_ok=True)
            print(f"DEBUG MARKER 6.5: Output directory {output_dir} confirmed to exist")

            # Get absolute paths for clarity
            abs_output_dir = output_dir_path.absolute()
            abs_output_file = output_file.absolute()
            print(f"DEBUG MARKER 6.6: Absolute output dir: {abs_output_dir}")
            print(f"DEBUG MARKER 6.7: Absolute output file: {abs_output_file}")

            # Write to a temporary file first in case of issues
            temp_output_file = abs_output_file.with_suffix(".tmp")
            print(f"DEBUG MARKER 6.8: Writing to temporary file: {temp_output_file}")
            with open(temp_output_file, "w") as f:
                json.dump(final_output, f, indent=2)

            # If successful, rename to the final file
            if temp_output_file.exists():
                print(
                    f"DEBUG MARKER 6.9: Temporary file created successfully, renaming"
                )
                temp_output_file.rename(abs_output_file)
                logger.info(f"Successfully saved results to {output_file}")
                print(f"DEBUG MARKER 7: Successfully saved to {output_file}")
            else:
                print(
                    f"DEBUG MARKER ERROR: Temporary file {temp_output_file} not created"
                )
                logger.error(f"Error saving results: temporary file not created")
                return False

        except Exception as e:
            logger.error(f"Error saving results to {output_file}: {e}", exc_info=True)
            # DEBUG MARKER 8
            print(f"DEBUG MARKER 8: Error saving to {output_file}: {e}")
            return False

        logger.info(f"COMPLETED processing {question_id_short} successfully")
        # DEBUG MARKER 9
        print(f"DEBUG MARKER 9: COMPLETED processing {question_id_short}")
        return True

    except Exception as e:
        logger.error(
            f"Unexpected error processing {file_path}: {str(e)}", exc_info=True
        )
        # DEBUG MARKER 10
        print(f"DEBUG MARKER 10: Unexpected error processing {file_path}: {str(e)}")
        return False


def process_all_proposals(
    proposals_dir,
    output_dir,
    max_concurrent,
    max_iterations,
    sample_size=0,
    use_spinner=True,
    timeout=900,
):
    """Process all proposal files with concurrent threads."""
    global spinner_manager

    logger.info(f"=== STARTING BATCH PROCESSING ===")
    logger.info(f"Processing proposals from {proposals_dir}")
    logger.info(f"Saving outputs to {output_dir}")
    logger.info(f"Using maximum of {max_concurrent} concurrent requests")
    logger.info(f"Maximum iterations per proposal: {max_iterations}")
    print(f"DEBUG-PROCESS-1: Starting batch processing with timeout {timeout} seconds")

    # Disable spinner if requested
    if not use_spinner:
        logger.info("Spinner UI disabled")

        # Create a dummy spinner that does nothing
        class DummySpinner:
            def add_spinner(self, *args, **kwargs):
                pass

            def update_spinner(self, *args, **kwargs):
                pass

            def remove_spinner(self, *args, **kwargs):
                pass

            def start(self, *args, **kwargs):
                pass

            def stop(self, *args, **kwargs):
                pass

        spinner_manager = DummySpinner()

    # Create output directory
    logger.info(f"Ensuring output directory exists: {output_dir}")
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory created/verified: {output_dir}")
    except Exception as e:
        logger.error(f"Failed to create output directory: {e}", exc_info=True)
        print(f"Error: Failed to create output directory: {e}")
        return 0, 1, 0

    # Collect all proposal files
    logger.info(f"Scanning for proposal files in {proposals_dir}")
    try:
        proposal_files = list(Path(proposals_dir).glob("*.json"))
        logger.info(f"Found {len(proposal_files)} proposal files")
    except Exception as e:
        logger.error(f"Failed to scan proposals directory: {e}", exc_info=True)
        print(f"Error: Failed to scan proposals directory: {e}")
        return 0, 1, 0

    # Sample if requested
    if sample_size > 0 and sample_size < len(proposal_files):
        try:
            import random

            logger.info(
                f"Sampling {sample_size} files from {len(proposal_files)} total files"
            )
            proposal_files = random.sample(proposal_files, sample_size)
            logger.info(f"Selected {len(proposal_files)} files for processing")
        except Exception as e:
            logger.error(f"Error during sampling: {e}", exc_info=True)
            print(f"Error during sampling: {e}")
            return 0, 1, 0

    # Setup counters
    processed_count = 0
    error_count = 0
    timeout_count = 0
    start_time = time.time()

    # Process files with a thread pool
    logger.info(f"Creating thread pool with {max_concurrent} workers")
    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        # Submit all tasks
        logger.info(
            f"[DEBUG] Submitting {len(proposal_files)} tasks to thread pool at {datetime.now().strftime('%H:%M:%S.%f')}"
        )
        future_to_file = {
            executor.submit(
                process_proposal_file, file_path, output_dir, max_iterations
            ): file_path
            for file_path in proposal_files
        }

        logger.info(f"Submitted {len(future_to_file)} tasks to the thread pool")
        print(
            f"DEBUG-PROCESS-2: Submitted {len(future_to_file)} tasks to the thread pool"
        )

        # Process results as they complete
        for future in future_to_file:
            file_path = future_to_file[future]
            file_name = os.path.basename(file_path)

            try:
                logger.info(
                    f"[DEBUG] Waiting for completion of {file_name} at {datetime.now().strftime('%H:%M:%S.%f')}"
                )
                print(
                    f"DEBUG-PROCESS-3: About to wait for {file_name} with {timeout}s timeout"
                )

                # Set a maximum time per proposal
                wait_start = time.time()
                print(f"DEBUG-PROCESS-4: Starting future.result() call for {file_name}")
                success = future.result(
                    timeout=timeout
                )  # Wait for completion with timeout
                wait_duration = time.time() - wait_start
                print(
                    f"DEBUG-PROCESS-5: future.result() completed for {file_name} after {wait_duration:.2f}s"
                )

                logger.info(
                    f"[DEBUG] Wait for {file_name} completed after {wait_duration:.2f}s at {datetime.now().strftime('%H:%M:%S.%f')}"
                )

                if success:
                    processed_count += 1
                    logger.info(
                        f"Successfully processed {file_name} ({processed_count}/{len(proposal_files)}) at {datetime.now().strftime('%H:%M:%S.%f')}"
                    )
                    print(f"✓ Successfully processed {file_name}")
                else:
                    error_count += 1
                    logger.error(
                        f"Failed to process {file_name} ({error_count} errors so far) at {datetime.now().strftime('%H:%M:%S.%f')}"
                    )
                    print(f"✗ Failed to process {file_name}")

            except concurrent.futures.TimeoutError:
                # This is the correct exception type for ThreadPoolExecutor timeouts
                timeout_count += 1
                timeout_minutes = timeout / 60
                print(f"DEBUG-PROCESS-TIMEOUT: Timeout occurred for {file_name}")
                logger.error(
                    f"Processing {file_name} timed out after {timeout_minutes:.1f} minutes (timeout #{timeout_count}) at {datetime.now().strftime('%H:%M:%S.%f')}"
                )
                print(
                    f"⏱ Timeout processing {file_name} after {timeout_minutes:.1f} minutes"
                )

                # Try to save whatever results we have so far
                logger.info(f"Attempting emergency save for {file_name}")
                if force_save_results(file_path, output_dir):
                    print(f"✓ Emergency save successful for {file_name}")
                    processed_count += 1
                else:
                    print(f"✗ Emergency save failed for {file_name}")
                    error_count += 1

                # Try to cancel the future if possible
                try:
                    logger.info(
                        f"Attempting to cancel processing of {file_name} at {datetime.now().strftime('%H:%M:%S.%f')}"
                    )
                    cancel_result = future.cancel()
                    logger.info(
                        f"Cancel result for {file_name}: {cancel_result} at {datetime.now().strftime('%H:%M:%S.%f')}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error cancelling future for {file_name}: {e} at {datetime.now().strftime('%H:%M:%S.%f')}"
                    )

            except Exception as e:
                error_count += 1
                print(f"DEBUG-PROCESS-ERROR: Exception for {file_name}: {e}")
                logger.error(
                    f"Error in thread processing {file_name}: {str(e)} at {datetime.now().strftime('%H:%M:%S.%f')}",
                    exc_info=True,
                )
                print(f"✗ Error processing {file_name}: {str(e)}")

    # Calculate statistics
    elapsed_time = time.time() - start_time
    runtime_minutes = elapsed_time / 60
    proposals_per_minute = processed_count / max(1, runtime_minutes)

    logger.info(f"=== PROCESSING COMPLETE ===")
    logger.info(f"Total files: {len(proposal_files)}")
    logger.info(f"Successfully processed: {processed_count}")
    logger.info(f"Errors: {error_count}")
    logger.info(f"Timeouts: {timeout_count}")
    logger.info(f"Total runtime: {runtime_minutes:.2f} minutes")
    logger.info(f"Processing rate: {proposals_per_minute:.2f} proposals/minute")
    print(
        f"DEBUG-PROCESS-COMPLETE: Processing complete with {processed_count} successes, {error_count} errors, {timeout_count} timeouts"
    )

    return processed_count, error_count, timeout_count


def force_save_results(file_path, output_dir):
    """Emergency function to save partial results when a timeout occurs."""
    try:
        file_name = os.path.basename(file_path)
        logger.info(f"EMERGENCY: Force saving partial results for {file_name}")

        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Load proposal data
        with open(file_path, "r") as f:
            proposal_data = json.load(f)

        # Extract basic data
        query_id = get_query_id_from_proposal(proposal_data)
        question_id_short = get_question_id_short(query_id)

        # Format prompts
        user_prompt = format_prompt_from_json(proposal_data)
        system_prompt = get_system_prompt()

        # Extract raw data
        if isinstance(proposal_data, list) and len(proposal_data) > 0:
            raw_data = proposal_data[0]
        else:
            raw_data = proposal_data

        # Create minimal result structure
        minimal_result = {
            "query_id": query_id,
            "question_id_short": question_id_short,
            "transaction_hash": raw_data.get("transaction_hash", ""),
            "user_prompt": user_prompt,
            "system_prompt": system_prompt,
            "processed_file": file_name,
            "emergency_save": True,
            "timestamp": time.time(),
            "error": "Emergency save due to timeout",
            "iterations": [],
            "total_iterations": 0,
            "recommendation": "None",
        }

        # Add proposal metadata
        minimal_result["proposal_metadata"] = {
            "creator": raw_data.get("creator", ""),
            "proposal_bond": raw_data.get("proposal_bond", 0),
            "reward_amount": raw_data.get("reward_amount", 0),
            "unix_timestamp": raw_data.get("unix_timestamp", 0),
            "block_number": raw_data.get("block_number", 0),
            "updates": raw_data.get("updates", []),
            "ancillary_data_hex": raw_data.get("ancillary_data_hex", ""),
        }

        # Save to file
        output_file = Path(output_dir) / get_output_filename(question_id_short)
        with open(output_file, "w") as f:
            json.dump(minimal_result, f, indent=2)

        logger.info(f"EMERGENCY: Successfully saved minimal results to {output_file}")
        return True
    except Exception as e:
        logger.error(f"EMERGENCY: Failed to save partial results: {e}", exc_info=True)
        return False


def main():
    """Main entry point."""
    args = parse_arguments()

    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)

    logger.info("=== COMBINATORIAL POST PROPOSAL RE-RUNNER STARTED ===")

    # Check API keys
    if not PERPLEXITY_API_KEY:
        logger.error(
            "ERROR: Perplexity API key not found. Please set PERPLEXITY_API_KEY in .env file."
        )
        print(
            "ERROR: Perplexity API key not found. Please set PERPLEXITY_API_KEY in .env file."
        )
        sys.exit(1)

    # Only check ChatGPT API key if we're not in perplexity-only mode
    if not args.perplexity_only and not CHATGPT_API_KEY:
        logger.error(
            "ERROR: ChatGPT API key not found. Please set OPENAI_API_KEY in .env file."
        )
        print(
            "ERROR: ChatGPT API key not found. Please set OPENAI_API_KEY in .env file."
        )
        sys.exit(1)

    # Clamp max_iterations to 0-3
    max_iterations = max(0, min(3, args.max_iterations))
    if max_iterations != args.max_iterations:
        logger.warning(
            f"Clamped max_iterations from {args.max_iterations} to {max_iterations}"
        )

    # If in perplexity-only mode, force max_iterations to 0
    if args.perplexity_only:
        logger.info("Running in Perplexity-only mode (skipping ChatGPT evaluation)")
        max_iterations = 0
        print("Running in Perplexity-only mode")

    try:
        logger.info("Starting proposal processing")
        processed, errors, timeouts = process_all_proposals(
            args.proposals_dir,
            args.output_dir,
            args.max_concurrent,
            max_iterations,
            args.sample_size,
            not args.disable_spinner,
            args.timeout,
        )

        # Log final summary
        logger.info(
            f"Processing complete: {processed} processed, {errors} errors, {timeouts} timeouts"
        )

        if processed > 0:
            logger.info("At least one proposal was processed successfully!")
            print(
                f"\nProcessing complete: {processed} processed, {errors} errors, {timeouts} timeouts"
            )
            print(f"Results saved to: {args.output_dir}")
            print("Success!")
            sys.exit(0)
        else:
            logger.error("Failed to process any proposals successfully.")
            print("\nFAILURE: No proposals were processed successfully.")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error in main process: {e}", exc_info=True)
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)
    finally:
        # Make sure all spinners are cleaned up
        try:
            spinner_manager.stop()
            logger.info("Spinner manager stopped")
        except Exception as e:
            logger.error(f"Error stopping spinner manager: {e}")

        logger.info("=== SCRIPT EXECUTION COMPLETED ===")


if __name__ == "__main__":
    main()
