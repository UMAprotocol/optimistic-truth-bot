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
from pathlib import Path
from datetime import datetime
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import only what we need from common to avoid web3 dependency issues
try:
    from common import (
        setup_logging,
        query_perplexity,
        extract_recommendation,
        spinner_animation,
    )
except ImportError:
    # Define minimal versions of these functions if imports fail
    def setup_logging(name, logfile=None):
        import logging

        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        if logfile:
            file_handler = logging.FileHandler(logfile)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        return logger

    def query_perplexity(prompt, api_key, verbose=False):
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        # Add necessary attributes to mimic Perplexity response
        response.citations = []
        return response

    def extract_recommendation(text):
        for line in text.split("\n"):
            if line.strip().startswith("recommendation:"):
                return line.split(":", 1)[1].strip()
        return None


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

    def start(self):
        """Start the spinner thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

        # Print empty lines to make space for spinners
        for _ in range(self.max_lines):
            print()
        # Move cursor back up
        print(f"\033[{self.max_lines}A", end="", flush=True)

    def stop(self):
        """Stop the spinner thread."""
        self.running = False
        if self.thread:
            self.thread.join()

        # Clear all spinner lines
        with self.lock:
            for line in range(self.max_lines):
                # Move to line, clear it, and reset cursor
                print(f"\033[{line+1};1H\033[K", end="", flush=True)

            # Move cursor to the bottom
            print(f"\033[{self.max_lines}B", end="", flush=True)

    def add_spinner(self, process_id, text):
        """Add a new spinner for a process."""
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

    def update_spinner(self, process_id, text):
        """Update the text for an existing spinner."""
        with self.lock:
            if process_id in self.active_spinners:
                self.active_spinners[process_id]["text"] = text

    def remove_spinner(self, process_id):
        """Remove a spinner."""
        with self.lock:
            if process_id in self.active_spinners:
                line = self.line_map[process_id]
                # Clear the line
                print(f"\033[{line+1};1H\033[K", end="", flush=True)
                del self.active_spinners[process_id]
                del self.line_map[process_id]

                if not self.active_spinners:
                    self.stop()

    def _spin(self):
        """Spinner animation loop."""
        while self.running and self.active_spinners:
            with self.lock:
                for process_id, spinner in self.active_spinners.items():
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

            time.sleep(0.1)


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

    def wait_if_needed(self):
        """Wait if needed to comply with rate limits. Returns wait time in seconds."""
        with self.lock:
            now = time.time()

            # If we haven't made enough requests yet, no need to wait
            if len(self.request_timestamps) < self.max_requests:
                self.request_timestamps.append(now)
                return 0

            # Check if the oldest request is more than 60 seconds old
            oldest_request_time = self.request_timestamps[0]
            time_since_oldest = now - oldest_request_time

            if time_since_oldest < 60:
                # Need to wait until the oldest request is 60 seconds old
                wait_time = 60 - time_since_oldest
                logger.info(
                    f"{self.name} rate limit reached. Waiting {wait_time:.2f} seconds before next request"
                )
                time.sleep(wait_time)
                now = time.time()  # Update time after waiting

            # Remove the oldest timestamp and add the new one
            self.request_timestamps.popleft()
            self.request_timestamps.append(now)

            return max(0, 60 - time_since_oldest)

    def increment_in_flight(self):
        """Increment the count of in-flight requests."""
        with self.in_flight_lock:
            self.in_flight += 1
            return self.in_flight

    def decrement_in_flight(self):
        """Decrement the count of in-flight requests."""
        with self.in_flight_lock:
            self.in_flight -= 1
            return self.in_flight

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
    return f"{question_id_short}_combinatorial.json"


def is_already_processed(question_id_short, output_dir):
    """Check if a proposal has already been processed."""
    return (Path(output_dir) / get_output_filename(question_id_short)).exists()


def query_chatgpt(prompt, api_key):
    """Query ChatGPT with a prompt."""
    try:
        # Wait if needed to respect rate limits
        chatgpt_rate_limiter.wait_if_needed()
        chatgpt_rate_limiter.increment_in_flight()

        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error querying ChatGPT: {e}")
        return None
    finally:
        chatgpt_rate_limiter.decrement_in_flight()


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
    results = {
        "question_id_short": question_id_short,
        "original_user_prompt": user_prompt,
        "system_prompt": system_prompt,
        "iterations": [],
    }

    current_iteration = 0
    current_user_prompt = user_prompt
    original_response = None
    recommendation = None

    while current_iteration <= max_iterations:
        iteration_result = {
            "iteration": current_iteration,
            "user_prompt": current_user_prompt,
        }

        # Add a spinner for this Perplexity query
        perplexity_process_id = f"{question_id_short}-perplexity-{current_iteration}"
        spinner_manager.add_spinner(
            perplexity_process_id,
            f"[{question_id_short}] Querying Perplexity (iteration {current_iteration})",
        )

        try:
            # Wait if needed to respect rate limits
            perplexity_rate_limiter.wait_if_needed()
            perplexity_rate_limiter.increment_in_flight()

            # Query Perplexity
            perplexity_start_time = time.time()
            perplexity_response = query_perplexity(
                current_user_prompt, PERPLEXITY_API_KEY, verbose=False
            )
            perplexity_time = time.time() - perplexity_start_time

            response_text = perplexity_response.choices[0].message.content
            citations = (
                [citation for citation in perplexity_response.citations]
                if hasattr(perplexity_response, "citations")
                else []
            )
            current_recommendation = extract_recommendation(response_text)

            # Store the original response for reference in future iterations
            if current_iteration == 0:
                original_response = response_text
                recommendation = current_recommendation

            # Record Perplexity response in this iteration
            iteration_result["perplexity_response"] = {
                "response": response_text,
                "recommendation": current_recommendation,
                "citations": citations,
                "api_time_seconds": perplexity_time,
                "model": perplexity_response.model,
                "token_usage": {
                    "completion_tokens": perplexity_response.usage.completion_tokens,
                    "prompt_tokens": perplexity_response.usage.prompt_tokens,
                    "total_tokens": perplexity_response.usage.total_tokens,
                },
            }

            logger.info(
                f"[{question_id_short}] Perplexity response received in {perplexity_time:.2f}s "
                f"(iteration {current_iteration}, recommendation: {current_recommendation})"
            )

        except Exception as e:
            logger.error(f"[{question_id_short}] Error querying Perplexity: {e}")
            iteration_result["perplexity_error"] = str(e)
            break
        finally:
            # Remove the Perplexity spinner
            spinner_manager.remove_spinner(perplexity_process_id)
            perplexity_rate_limiter.decrement_in_flight()

        # If this is the last allowed iteration, don't bother asking ChatGPT for evaluation
        if current_iteration >= max_iterations:
            iteration_result["is_final"] = True
            results["iterations"].append(iteration_result)
            break

        # Create ChatGPT evaluation prompt based on iteration
        if current_iteration == 0:
            chatgpt_prompt = create_chatgpt_evaluation_prompt(
                user_prompt, system_prompt, response_text
            )
        else:
            chatgpt_prompt = create_chatgpt_follow_up_evaluation_prompt(
                user_prompt,
                system_prompt,
                original_response,
                current_user_prompt,  # This is the follow-up prompt from last iteration
                response_text,
            )

        # Add a spinner for the ChatGPT evaluation
        chatgpt_process_id = f"{question_id_short}-chatgpt-{current_iteration}"
        spinner_manager.add_spinner(
            chatgpt_process_id,
            f"[{question_id_short}] Evaluating with ChatGPT (iteration {current_iteration})",
        )

        try:
            # Query ChatGPT for evaluation
            chatgpt_start_time = time.time()
            chatgpt_response = query_chatgpt(chatgpt_prompt, CHATGPT_API_KEY)
            chatgpt_time = time.time() - chatgpt_start_time

            # Parse ChatGPT's response
            is_satisfied, follow_up_prompt = parse_chatgpt_response(chatgpt_response)

            # Record ChatGPT evaluation in this iteration
            iteration_result["chatgpt_evaluation"] = {
                "prompt": chatgpt_prompt,
                "response": chatgpt_response,
                "is_satisfied": is_satisfied,
                "follow_up_prompt": follow_up_prompt,
                "api_time_seconds": chatgpt_time,
            }

            logger.info(
                f"[{question_id_short}] ChatGPT evaluation received in {chatgpt_time:.2f}s "
                f"(iteration {current_iteration}, satisfied: {is_satisfied})"
            )

        except Exception as e:
            logger.error(f"[{question_id_short}] Error querying ChatGPT: {e}")
            iteration_result["chatgpt_error"] = str(e)
            break
        finally:
            # Remove the ChatGPT spinner
            spinner_manager.remove_spinner(chatgpt_process_id)

        # Record this iteration
        results["iterations"].append(iteration_result)

        # If ChatGPT is satisfied, we're done
        if is_satisfied or not follow_up_prompt:
            break

        # Otherwise, prepare for next iteration
        current_iteration += 1
        current_user_prompt = follow_up_prompt

    # Add final recommendation and summary stats
    results["final_recommendation"] = recommendation
    results["total_iterations"] = len(results["iterations"])
    results["timestamp"] = time.time()

    return results


def process_proposal_file(file_path, output_dir, max_iterations):
    """Process a single proposal file."""
    file_name = os.path.basename(file_path)
    logger.info(f"Processing proposal: {file_name}")

    try:
        # Load proposal data
        with open(file_path, "r") as f:
            proposal_data = json.load(f)

        # Extract query ID and check if already processed
        query_id = get_query_id_from_proposal(proposal_data)
        question_id_short = get_question_id_short(query_id)

        if query_id and is_already_processed(question_id_short, output_dir):
            logger.info(f"Proposal {question_id_short} already processed, skipping")
            return True

        # Format the user prompt
        user_prompt = format_prompt_from_json(proposal_data)

        # Get the system prompt
        system_prompt = get_system_prompt()

        # Extract metadata from proposal
        if isinstance(proposal_data, list) and len(proposal_data) > 0:
            raw_data = proposal_data[0]
        else:
            raw_data = proposal_data

        # Run the iterative prompting process
        logger.info(
            f"Starting iterative prompting for {question_id_short} with max {max_iterations} iterations"
        )
        results = run_iterative_prompting(
            question_id_short, user_prompt, system_prompt, max_iterations
        )

        # Create the proposal metadata (only what should be nested)
        proposal_metadata = {
            "query_id": query_id,
            "question_id_short": question_id_short,
            "transaction_hash": raw_data.get("transaction_hash", ""),
            "creator": raw_data.get("creator", ""),
            "proposal_bond": raw_data.get("proposal_bond", 0),
            "reward_amount": raw_data.get("reward_amount", 0),
            "unix_timestamp": raw_data.get("unix_timestamp", 0),
            "block_number": raw_data.get("block_number", 0),
            "proposed_price": raw_data.get("proposed_price", None),
            "resolved_price": raw_data.get("resolved_price", None),
            "updates": raw_data.get("updates", []),
            "ancillary_data_hex": raw_data.get("ancillary_data_hex", ""),
        }

        # Get tags if they exist
        tags = raw_data.get("tags", [])

        # Create the final output with correct structure
        final_output = {
            # Root level keys
            "query_id": query_id,
            "question_id_short": question_id_short,
            "transaction_hash": raw_data.get("transaction_hash", ""),
            "user_prompt": user_prompt,
            "system_prompt": system_prompt,
            "processed_file": file_name,
            "proposal_metadata": proposal_metadata,
            "timestamp": results["timestamp"],
            "iterations": results["iterations"],
            "total_iterations": results["total_iterations"],
            "final_recommendation": results["final_recommendation"],
        }

        # Add response data from first iteration if available
        if results["iterations"] and "perplexity_response" in results["iterations"][0]:
            first_response = results["iterations"][0]["perplexity_response"]
            final_output["response"] = first_response.get("response", "")
            final_output["recommendation"] = first_response.get("recommendation", "")
            final_output["citations"] = first_response.get("citations", [])

            # Add response metadata
            final_output["response_metadata"] = {
                "model": first_response.get("model", ""),
                "created_timestamp": int(results["timestamp"]),
                "created_datetime": datetime.fromtimestamp(
                    results["timestamp"]
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

        # Add proposed and resolved price outcomes if available
        if "proposed_price" in raw_data and raw_data["proposed_price"] is not None:
            final_output["proposed_price"] = raw_data["proposed_price"]
            final_output["proposed_price_outcome"] = f"p{raw_data['proposed_price']}"

        if "resolved_price" in raw_data and raw_data["resolved_price"] is not None:
            final_output["resolved_price"] = raw_data["resolved_price"]
            final_output["resolved_price_outcome"] = f"p{raw_data['resolved_price']}"

        # Add tags if they exist
        if tags:
            final_output["tags"] = tags

        # Add disputed status if available
        if "disputed" in raw_data:
            final_output["disputed"] = raw_data["disputed"]

        # Save results with corrected structure
        output_file = Path(output_dir) / get_output_filename(question_id_short)
        with open(output_file, "w") as f:
            json.dump(final_output, f, indent=2)

        logger.info(
            f"Completed processing {question_id_short} with {results['total_iterations']} iterations. "
            f"Saved to {output_file}"
        )
        return True

    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        return False


def process_all_proposals(
    proposals_dir, output_dir, max_concurrent, max_iterations, sample_size=0
):
    """Process all proposal files with concurrent threads."""
    logger.info(f"Processing proposals from {proposals_dir}")
    logger.info(
        f"Using maximum of {max_concurrent} concurrent requests and {max_iterations} max iterations"
    )

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Collect all proposal files
    proposal_files = list(Path(proposals_dir).glob("*.json"))
    logger.info(f"Found {len(proposal_files)} proposal files")

    # Sample if requested
    if sample_size > 0 and sample_size < len(proposal_files):
        import random

        proposal_files = random.sample(proposal_files, sample_size)
        logger.info(f"Sampled {sample_size} files for processing")

    # Setup counters
    processed_count = 0
    error_count = 0
    start_time = time.time()

    # Process files with a thread pool
    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(
                process_proposal_file, file_path, output_dir, max_iterations
            ): file_path
            for file_path in proposal_files
        }

        # Process results as they complete
        for future in future_to_file:
            file_path = future_to_file[future]
            try:
                success = future.result()
                if success:
                    processed_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"Error in thread processing file {file_path}: {str(e)}")
                error_count += 1

    elapsed_time = time.time() - start_time
    runtime_minutes = elapsed_time / 60

    logger.info(
        f"Processing complete. Successful: {processed_count}, Errors: {error_count}"
    )
    logger.info(
        f"Total runtime: {runtime_minutes:.2f} minutes "
        f"(Average: {processed_count/max(1, runtime_minutes):.2f} proposals/minute)"
    )


def main():
    """Main entry point."""
    args = parse_arguments()

    # Check API keys
    if not PERPLEXITY_API_KEY:
        logger.error(
            "Perplexity API key not found. Please set PERPLEXITY_API_KEY in .env file."
        )
        sys.exit(1)

    if not CHATGPT_API_KEY:
        logger.error(
            "ChatGPT API key not found. Please set OPENAI_API_KEY in .env file."
        )
        sys.exit(1)

    # Clamp max_iterations to 0-3
    max_iterations = max(0, min(3, args.max_iterations))

    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)

    logger.info("Starting Combinatorial Post Proposal Re-runner")
    process_all_proposals(
        args.proposals_dir,
        args.output_dir,
        args.max_concurrent,
        max_iterations,
        args.sample_size,
    )
    logger.info("Combinatorial Post Proposal Re-runner finished")

    # Make sure all spinners are cleaned up
    spinner_manager.stop()


if __name__ == "__main__":
    main()
