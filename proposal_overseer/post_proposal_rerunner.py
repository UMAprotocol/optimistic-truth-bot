#!/usr/bin/env python3
"""
UMA Post Proposal Re-runner with ChatGPT Oversight - Processes existing proposals with Perplexity-ChatGPT validation loop.
Usage: python proposal_overseer/post_proposal_rerunner.py [--proposals-dir PATH] [--output-dir PATH] [--max-concurrent N] [--max-attempts N]
"""

import os
import json
import time
import threading
import sys
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import re

# Parse command line arguments
parser = argparse.ArgumentParser(
    description="UMA Post Proposal Re-runner with ChatGPT Oversight"
)
parser.add_argument(
    "--proposals-dir",
    type=str,
    help="Directory containing proposal JSON files to process",
)
parser.add_argument("--output-dir", type=str, help="Directory to store output files")
parser.add_argument(
    "--max-concurrent",
    type=int,
    default=5,
    help="Maximum number of concurrent API requests",
)
parser.add_argument(
    "--max-attempts",
    type=int,
    default=3,
    help="Maximum number of attempts to query Perplexity with ChatGPT validation",
)
parser.add_argument(
    "--start-block",
    type=int,
    default=0,
    help="Starting block number to process proposals from",
)
parser.add_argument(
    "--min-attempts",
    type=int,
    default=2,
    help="Minimum number of attempts before defaulting to p4",
)
parser.add_argument(
    "--verbose",
    action="store_true",
    help="Enable verbose output with progress updates",
)
args = parser.parse_args()

print(
    "🔍 Starting UMA Post Proposal Re-runner with ChatGPT Oversight - Processing existing proposals 🤖 📊"
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompt import get_system_prompt

# Import locally defined modules
from proposal_overseer.common import (
    setup_logging,
    extract_recommendation,
    query_perplexity,
    query_chatgpt,
    extract_prompt_update,
    get_overseer_decision,
    enhanced_perplexity_chatgpt_loop,
)

logger = setup_logging("post_proposal_rerunner", "logs/post_proposal_rerunner.log")
load_dotenv()
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Verify API keys are available
if not PERPLEXITY_API_KEY:
    logger.error("PERPLEXITY_API_KEY not found in environment variables")
    sys.exit(1)

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not found in environment variables")
    sys.exit(1)

# Set the proposals directory - use command line argument if provided, otherwise use default
PROPOSALS_DIR = (
    Path(args.proposals_dir)
    if args.proposals_dir
    else Path(__file__).parent / "proposals"
)
# Use command line argument for output directory if provided, otherwise use default
OUTPUTS_DIR = (
    Path(args.output_dir) if args.output_dir else Path(__file__).parent / "outputs"
)
OUTPUTS_DIR.mkdir(exist_ok=True)

# Ensure proposals directory exists
if not PROPOSALS_DIR.exists():
    logger.error(f"Proposals directory not found: {PROPOSALS_DIR}")
    sys.exit(1)

# Store the starting block number and max attempts
START_BLOCK_NUMBER = args.start_block
MAX_ATTEMPTS = args.max_attempts
MIN_ATTEMPTS = args.min_attempts
MAX_CONCURRENT = args.max_concurrent
VERBOSE = args.verbose

logger.info(f"Using starting block number: {START_BLOCK_NUMBER}")
logger.info(f"Proposals directory set to: {PROPOSALS_DIR}")
logger.info(f"Output directory set to: {OUTPUTS_DIR}")
logger.info(f"Maximum attempts set to: {MAX_ATTEMPTS}")
logger.info(f"Minimum attempts before defaulting to p4: {MIN_ATTEMPTS}")
logger.info(f"Maximum concurrent requests set to: {MAX_CONCURRENT}")
logger.info(f"Verbose logging: {'Enabled' if VERBOSE else 'Disabled'}")


# Progress tracking class
class ProgressTracker:
    """Thread-safe tracker for progress of proposal processing that logs when files are completed."""

    def __init__(self, total_items):
        self.total = total_items
        self.processed = 0
        self.api_calls = 0
        self.skipped = 0
        self.start_time = time.time()
        self.current_file = ""
        self.lock = threading.Lock()  # Add lock for thread safety

    def start(self):
        """Start the progress tracker."""
        logger.info(f"Starting to process {self.total} files")
        if VERBOSE:
            print(f"Starting to process {self.total} files")

    def stop(self):
        """Stop the progress tracker and print final stats."""
        self._print_final_stats()

    def set_current_file(self, filename):
        """Set the current file being processed."""
        with self.lock:
            self.current_file = filename
            if VERBOSE:
                print(f"Processing: {filename}")

    def increment(self, processed=False, api_call=False, skipped=False):
        """Thread-safe increment of counters and log progress when a file is processed."""
        with self.lock:
            if processed:
                self.processed += 1
                self._log_file_completion(is_skip=False)
            if api_call:
                self.api_calls += 1
            if skipped:
                self.skipped += 1
                self._log_file_completion(is_skip=True)

    def _log_file_completion(self, is_skip=False):
        """Log progress when a file is completed."""
        # This method is called within increment() which already has the lock
        elapsed = time.time() - self.start_time
        minutes = elapsed / 60
        percent = (self.processed / self.total) * 100 if self.total > 0 else 0

        if VERBOSE:
            # Detailed output for verbose mode
            msg = (
                f"Progress: {self.processed}/{self.total} ({percent:.1f}%) - "
                f"API calls: {self.api_calls} - "
                f"Skipped: {self.skipped} - "
                f"Elapsed: {minutes:.1f} min - "
                f"Completed: {self.current_file}"
            )
            print(msg, flush=True)
            logger.info(msg)
        else:
            # In non-verbose mode, only print for non-skipped files or every 10 skipped files
            if not is_skip or self.skipped % 10 == 0:
                msg = f"Processing: {self.processed}/{self.total} ({percent:.1f}%) - Skipped: {self.skipped} - Completed: {self.current_file}"
                print(msg, flush=True)
                if not is_skip:  # Only log non-skipped files to avoid log spam
                    logger.info(msg)

    def _print_final_stats(self):
        """Print final statistics."""
        with self.lock:
            elapsed = time.time() - self.start_time
            minutes = elapsed / 60
            msg = f"Completed: {self.processed}/{self.total} proposals - API calls: {self.api_calls} - Skipped: {self.skipped} - Time: {minutes:.1f} min"
            print(msg, flush=True)
            logger.info(msg)


class RateLimiter:
    """Rate limiter for API calls with a maximum of N requests per minute.
    Enhanced to handle concurrent requests properly."""

    def __init__(self, max_requests_per_minute=5, max_concurrent=5):
        self.max_requests = max_requests_per_minute
        self.max_concurrent = max_concurrent
        self.request_timestamps = deque(maxlen=max_requests_per_minute)
        self.lock = threading.Lock()  # Lock for timestamps
        self.in_flight = 0
        self.in_flight_lock = threading.Lock()  # Lock for tracking in-flight requests
        self.concurrency_semaphore = threading.Semaphore(
            max_concurrent
        )  # Limit concurrent processing

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
                    f"Rate limit reached. Waiting {wait_time:.2f} seconds before next request"
                )
                time.sleep(wait_time)
                now = time.time()  # Update time after waiting

            # Remove the oldest timestamp and add the new one
            self.request_timestamps.popleft()
            self.request_timestamps.append(now)

            return max(0, 60 - time_since_oldest)

    def acquire(self):
        """Acquire permission to make an API request, handling both rate limiting and concurrency."""
        # First, acquire the concurrency semaphore (blocks if max concurrent requests are in progress)
        self.concurrency_semaphore.acquire()

        try:
            # Then, wait if needed to respect rate limits
            wait_time = self.wait_if_needed()

            # Track the in-flight request
            with self.in_flight_lock:
                self.in_flight += 1
                current_in_flight = self.in_flight

            return wait_time, current_in_flight
        except Exception as e:
            # If anything goes wrong, release the semaphore
            self.concurrency_semaphore.release()
            raise e

    def release(self):
        """Release resources after an API request is complete."""
        try:
            # Update in-flight counter
            with self.in_flight_lock:
                # Ensure we don't go below zero
                if self.in_flight > 0:
                    self.in_flight -= 1
                else:
                    self.in_flight = 0
                current_in_flight = self.in_flight

            # Release the concurrency semaphore
            self.concurrency_semaphore.release()

            return current_in_flight
        except Exception as e:
            logger.error(f"Error releasing rate limiter: {e}")
            return 0

    def increment_in_flight(self):
        """Increment the count of in-flight requests (legacy method)."""
        with self.in_flight_lock:
            self.in_flight += 1
            return self.in_flight

    def decrement_in_flight(self):
        """Decrement the count of in-flight requests (legacy method)."""
        with self.in_flight_lock:
            self.in_flight -= 1
            return self.in_flight

    def get_in_flight(self):
        """Get the current number of in-flight requests."""
        with self.in_flight_lock:
            return self.in_flight


# Create a global rate limiter instance
perplexity_rate_limiter = RateLimiter(
    max_requests_per_minute=5, max_concurrent=MAX_CONCURRENT
)


def format_prompt_from_json(proposal_data):
    if isinstance(proposal_data, list) and len(proposal_data) > 0:
        proposal_data = proposal_data[0]

    ancillary_data = proposal_data.get("ancillary_data", "")
    resolution_conditions = proposal_data.get("resolution_conditions", "")
    updates = proposal_data.get("updates", [])

    prompt = f"user:\n\nancillary_data:\n{ancillary_data}\n\n"
    if resolution_conditions:
        prompt += f"resolution_conditions:\n{resolution_conditions}\n\n"
    if updates:
        prompt += f"updates:\n{updates}"
    return prompt


def get_query_id_from_proposal(proposal_data):
    if isinstance(proposal_data, list) and len(proposal_data) > 0:
        return proposal_data[0].get("query_id", "")
    return proposal_data.get("query_id", "")


def get_question_id_short(query_id):
    if not query_id:
        return "unknown"
    return query_id[2:10] if query_id.startswith("0x") else query_id[:8]


def get_output_filename(query_id):
    return f"{get_question_id_short(query_id)}.json"


def is_already_processed(query_id):
    if not query_id:
        return False
    return (OUTPUTS_DIR / get_output_filename(query_id)).exists()


def get_block_number_from_proposal(proposal_data):
    if isinstance(proposal_data, list) and len(proposal_data) > 0:
        return proposal_data[0].get("block_number", 0)
    return proposal_data.get("block_number", 0)


def should_process_proposal(proposal_data):
    # Check if the block number is greater than or equal to our starting block
    block_number = get_block_number_from_proposal(proposal_data)
    return block_number >= START_BLOCK_NUMBER


def process_proposal_file(file_path, progress_tracker):
    file_name = os.path.basename(file_path)
    file_process_start_time = time.time()

    # Update current file in progress tracker
    progress_tracker.set_current_file(file_name)

    # Log file processing start - only to file, not to console unless verbose
    if VERBOSE:
        logger.info(f"Processing proposal: {file_name}")
    else:
        logger.debug(f"Processing proposal: {file_name}")

    try:
        # Open and parse the proposal file
        with open(file_path, "r") as f:
            proposal_data = json.load(f)

        # Check if we should process this proposal based on block number
        if not should_process_proposal(proposal_data):
            logger.info(
                f"Skipping proposal with block number below {START_BLOCK_NUMBER}"
            )
            progress_tracker.increment(skipped=True)
            return True, False  # Processed (skipped), but no API call made

        # Check if already processed
        query_id = get_query_id_from_proposal(proposal_data)
        if query_id and is_already_processed(query_id):
            if VERBOSE:
                logger.info(f"Proposal {query_id} already processed, skipping")
            else:
                logger.debug(f"Proposal {query_id} already processed, skipping")
            progress_tracker.increment(skipped=True)
            return True, False  # Processed (skipped), but no API call made

        # Setup inputs for API calls
        user_prompt = format_prompt_from_json(proposal_data)
        system_prompt = get_system_prompt()

        is_list = isinstance(proposal_data, list) and len(proposal_data) > 0
        tx_hash = (proposal_data[0] if is_list else proposal_data).get(
            "transaction_hash", ""
        )
        price = (proposal_data[0] if is_list else proposal_data).get(
            "proposed_price", None
        )

        # Acquire permission to make API request (handles both rate limiting and concurrency)
        try:
            wait_time, in_flight = perplexity_rate_limiter.acquire()

            if wait_time > 0:
                logger.info(
                    f"Rate limit reached. Waiting {wait_time:.2f} seconds before querying for {get_question_id_short(query_id)}"
                )
                if VERBOSE:
                    print(f"Rate limited: waited {wait_time:.2f}s before querying")

            # Log the request start
            api_msg = f"Starting Perplexity-ChatGPT loop for {get_question_id_short(query_id)} (in-flight: {in_flight})"
            logger.info(api_msg)
            if VERBOSE:
                print(api_msg)

            start_time = time.time()
            result = None

            # Make API calls
            try:
                result = enhanced_perplexity_chatgpt_loop(
                    user_prompt=user_prompt,
                    perplexity_api_key=PERPLEXITY_API_KEY,
                    chatgpt_api_key=OPENAI_API_KEY,
                    original_system_prompt=system_prompt,
                    logger=logger,
                    max_attempts=MAX_ATTEMPTS,
                    min_attempts=MIN_ATTEMPTS,
                    verbose=VERBOSE,
                )

                if VERBOSE:
                    print(f"API calls completed for {get_question_id_short(query_id)}")

                # Verify we have valid Perplexity responses before proceeding
                perplexity_responses = [
                    r
                    for r in result.get("responses", [])
                    if r.get("interaction_type") == "perplexity_query"
                ]
                if not perplexity_responses:
                    error_msg = f"No valid Perplexity responses for {get_question_id_short(query_id)}"
                    logger.error(error_msg)
                    if VERBOSE:
                        print(f"ERROR: {error_msg}")
                    raise Exception(error_msg)

            except Exception as api_error:
                # Clean up error message if it contains HTML
                error_msg = str(api_error)
                if len(error_msg) > 100 and (
                    "<html>" in error_msg or "401" in error_msg
                ):
                    error_msg = f"Perplexity API authentication error (401 Unauthorized) for {get_question_id_short(query_id)}"
                else:
                    error_msg = f"Error during API calls for {get_question_id_short(query_id)}: {error_msg}"

                logger.error(error_msg)
                if VERBOSE:
                    print(f"ERROR: {error_msg}")
                # Do not proceed if Perplexity API failed
                raise
            finally:
                # Release resources when done
                try:
                    in_flight = perplexity_rate_limiter.release()
                    api_complete_msg = f"Completed Perplexity-ChatGPT loop for {get_question_id_short(query_id)} (in-flight: {max(0, in_flight)})"
                    logger.info(api_complete_msg)
                except Exception as release_error:
                    logger.error(f"Error releasing rate limiter: {str(release_error)}")
                    logger.info(
                        f"Completed Perplexity-ChatGPT loop for {get_question_id_short(query_id)}"
                    )
        except Exception as acquire_error:
            error_msg = f"Error acquiring permission for {get_question_id_short(query_id)}: {str(acquire_error)}"
            logger.error(error_msg)
            if VERBOSE:
                print(f"ERROR: {error_msg}")
            raise

        if not result:
            error_msg = f"No result obtained from API calls for {get_question_id_short(query_id)}"
            logger.error(error_msg)
            if VERBOSE:
                print(f"ERROR: {error_msg}")
            raise Exception(error_msg)

        # Verify result has valid data structure before continuing
        if not result.get("final_recommendation") or not result.get("final_response"):
            error_msg = f"Invalid result format from API calls for {get_question_id_short(query_id)}"
            logger.error(error_msg)
            if VERBOSE:
                print(f"ERROR: {error_msg}")
            raise Exception(error_msg)

        api_response_time = time.time() - start_time
        logger.info(f"API responses received in {api_response_time:.2f} seconds")

        # Extract and organize proposal metadata
        if isinstance(proposal_data, list) and len(proposal_data) > 0:
            raw_data = proposal_data[0]
        else:
            raw_data = proposal_data

        proposal_metadata = {
            "creator": raw_data.get("creator", ""),
            "proposal_bond": raw_data.get("proposal_bond", 0),
            "reward_amount": raw_data.get("reward_amount", 0),
            "unix_timestamp": raw_data.get("unix_timestamp", 0),
            "block_number": raw_data.get("block_number", 0),
            "updates": raw_data.get("updates", []),
            "ancillary_data_hex": raw_data.get("ancillary_data_hex", ""),
        }

        # Prepare the output data with all the information we've gathered
        final_response = next(
            (
                r
                for r in reversed(result["responses"])
                if r.get("interaction_type") == "perplexity_query"
            ),
            None,
        )

        output_data = {
            "query_id": query_id,
            "question_id_short": get_question_id_short(query_id),
            "transaction_hash": tx_hash,
            "proposed_price": price,
            "resolved_price": None,
            "timestamp": time.time(),
            "processed_file": file_name,
            "proposal_metadata": proposal_metadata,
            "resolved_price_outcome": None,
            "disputed": False,
            "recommendation": result["final_recommendation"],
            "recommendation_overridden": result.get("recommendation_overridden", False),
            "proposed_price_outcome": extract_recommendation(result["final_response"]),
            "user_prompt": user_prompt,  # Include the user prompt in the output
            "system_prompt": system_prompt,  # Include the system prompt in the output
            "overseer_data": {
                "attempts": result["attempts"],
                "interactions": result["responses"],
                "recommendation_journey": [
                    {
                        "attempt": i + 1,
                        "perplexity_recommendation": next(
                            (
                                r["recommendation"]
                                for r in result["responses"]
                                if r.get("attempt") == i + 1
                                and r["interaction_type"] == "perplexity_query"
                            ),
                            None,
                        ),
                        "overseer_satisfaction_level": next(
                            (
                                r["satisfaction_level"]
                                for r in result["responses"]
                                if r.get("stage") == f"evaluation_{i+1}"
                                and r["interaction_type"] == "chatgpt_evaluation"
                            ),
                            None,
                        ),
                        "prompt_updated": next(
                            (
                                r["prompt_updated"]
                                for r in result["responses"]
                                if r.get("stage") == f"evaluation_{i+1}"
                                and r["interaction_type"] == "chatgpt_evaluation"
                            ),
                            False,
                        ),
                        "critique": next(
                            (
                                r["critique"]
                                for r in result["responses"]
                                if r.get("stage") == f"evaluation_{i+1}"
                                and r["interaction_type"] == "chatgpt_evaluation"
                            ),
                            None,
                        ),
                        "system_prompt_before": next(
                            (
                                r["system_prompt_before"]
                                for r in result["responses"]
                                if r.get("stage") == f"evaluation_{i+1}"
                                and r["interaction_type"] == "chatgpt_evaluation"
                            ),
                            None,
                        ),
                        "system_prompt_after": next(
                            (
                                r["system_prompt_after"]
                                for r in result["responses"]
                                if r.get("stage") == f"evaluation_{i+1}"
                                and r["interaction_type"] == "chatgpt_evaluation"
                            ),
                            None,
                        ),
                    }
                    for i in range(result["attempts"])
                ],
                "final_response_metadata": (
                    final_response.get("response_metadata")
                    if final_response and final_response.get("response_metadata")
                    else None
                ),
            },
        }

        # Include tags if they exist in the proposal data
        if "tags" in raw_data:
            output_data["tags"] = raw_data.get("tags", [])

        output_file = OUTPUTS_DIR / get_output_filename(query_id)
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        total_time = time.time() - file_process_start_time
        completion_msg = f"Output saved to {output_file} with recommendation: {output_data['recommendation']} (time: {total_time:.2f}s)"
        logger.info(completion_msg)
        if VERBOSE:
            print(completion_msg)

        progress_tracker.increment(processed=True, api_call=True)
        return True, True  # Processed and API call made

    except Exception as e:
        error_msg = f"Error processing {file_path}: {str(e)}"
        logger.error(error_msg)
        if VERBOSE:
            print(f"ERROR: {error_msg}")
        # Ensure we release resources even on error
        try:
            perplexity_rate_limiter.release()
        except:
            pass
        progress_tracker.increment(skipped=True)
        return False, False  # Not processed, no API call made


def process_all_proposals():
    logger.info(f"Processing all proposals from {PROPOSALS_DIR}")
    logger.info(f"Using concurrent processing with max_concurrent={MAX_CONCURRENT}")

    # Collect all proposal files first
    proposal_files = list(Path(PROPOSALS_DIR).glob("*.json"))
    total_files = len(proposal_files)

    logger.info(f"Found {total_files} proposal files to process")

    # Count already processed files
    processed_files_count = len(list(Path(OUTPUTS_DIR).glob("*.json")))
    if processed_files_count > 0:
        logger.info(
            f"Found {processed_files_count} already processed files in output directory"
        )

    # Check for valid API keys before processing
    if not PERPLEXITY_API_KEY or not OPENAI_API_KEY:
        logger.error("Missing API keys - cannot proceed")
        print("ERROR: Missing API keys - cannot proceed")
        return

    # Try a test API call to verify Perplexity API is working
    try:
        test_result = query_perplexity(
            "test query to verify API key",
            PERPLEXITY_API_KEY,
        )
        if not test_result or not isinstance(test_result, dict):
            logger.error("Perplexity API test failed - invalid response format")
            print("ERROR: Perplexity API test failed - invalid response format")
            sys.exit(1)  # Exit with error code
    except Exception as e:
        error_msg = str(e)
        # Don't log the full HTML response
        if (
            "401" in error_msg
            or "Authorization Required" in error_msg
            or "Unauthorized" in error_msg
        ):
            logger.error("Perplexity API authentication failed (401 Unauthorized)")
            print("ERROR: Perplexity API authentication failed (401 Unauthorized)")
        elif len(error_msg) > 100 and ("<html>" in error_msg or "<head>" in error_msg):
            logger.error(
                "Perplexity API returned HTML error response (authentication failed)"
            )
            print(
                "ERROR: Perplexity API returned HTML error response (authentication failed)"
            )
        else:
            # Only log non-HTML errors
            logger.error(f"Perplexity API test failed: {error_msg}")
            print(f"ERROR: Perplexity API test failed: {error_msg}")

        # Exit immediately on any API test failure
        logger.error(
            "Cannot proceed with invalid Perplexity API key or out of API credits"
        )
        print(
            "ERROR: Cannot proceed with invalid Perplexity API key or out of API credits"
        )
        sys.exit(1)  # Exit with error code

    # Create and start progress tracker
    progress_tracker = ProgressTracker(total_files)
    progress_tracker.start()

    # Log the start of file processing
    if VERBOSE:
        print(f"Starting to process files with {MAX_CONCURRENT} concurrent workers")

    # Create a lock for the progress tracker to prevent concurrent access issues
    progress_tracker_lock = threading.Lock()

    # Counter for consecutive API errors to detect persistent API issues
    consecutive_api_errors = 0
    consecutive_api_errors_lock = threading.Lock()
    MAX_CONSECUTIVE_API_ERRORS = 5  # Exit after this many consecutive API errors

    def process_file_with_lock(file_path):
        """Process a file with thread-safe progress tracking"""
        nonlocal consecutive_api_errors

        try:
            # Process the file
            processed, api_call_made = process_proposal_file(
                file_path, progress_tracker
            )

            # If API call was successful, reset consecutive error counter
            if api_call_made and processed:
                with consecutive_api_errors_lock:
                    consecutive_api_errors = 0

            # Update progress stats in a thread-safe manner
            with progress_tracker_lock:
                if VERBOSE and processed:
                    print(f"Completed processing {file_path.name}")

            return processed, api_call_made
        except Exception as e:
            error_str = str(e)

            # Check for HTML or authentication errors
            is_html_error = len(error_str) > 100 and (
                "<html>" in error_str or "<head>" in error_str
            )
            is_auth_error = (
                "401" in error_str
                or "Unauthorized" in error_str
                or "authorization" in error_str.lower()
            )

            # Create a clean error message
            if is_html_error or is_auth_error:
                error_msg = "Perplexity API authentication error (401 Unauthorized)"
                # If we encounter an authentication error, exit immediately
                logger.critical(
                    "CRITICAL: Authentication error with Perplexity API detected"
                )
                print("\nCRITICAL: Authentication error with Perplexity API detected")
                print("Exiting to prevent further API calls...\n")
                os._exit(1)  # Exit immediately
            else:
                error_msg = f"Error processing file {file_path}: {error_str}"

            logger.error(error_msg)
            print(f"ERROR: {error_msg}")

            # Check if this was an API error and increment counter
            if "API" in error_str or "Perplexity" in error_str:
                with consecutive_api_errors_lock:
                    consecutive_api_errors += 1
                    current_count = consecutive_api_errors

                # If we've had too many consecutive API errors, exit
                if current_count >= MAX_CONSECUTIVE_API_ERRORS:
                    critical_msg = f"CRITICAL: {current_count} consecutive API errors detected - possible API quota/auth issue"
                    logger.critical(critical_msg)
                    print(f"\n{critical_msg}")
                    print("Exiting to prevent further API calls...\n")
                    # Exit the entire program
                    os._exit(1)

            # Update progress stats in a thread-safe manner
            with progress_tracker_lock:
                progress_tracker.increment(skipped=True)

            return False, False

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
        # Submit all tasks to the executor
        future_to_file = {
            executor.submit(process_file_with_lock, file_path): file_path
            for file_path in proposal_files
        }

        # Process results as they complete
        for future in future_to_file:
            try:
                future.result()  # Wait for the task to complete
            except Exception as exc:
                file_path = future_to_file[future]
                logger.error(f"Task for {file_path} generated an exception: {exc}")
                with progress_tracker_lock:
                    progress_tracker.increment(skipped=True)

    # Stop the progress tracker to display final stats
    progress_tracker.stop()


def main():
    logger.info("Starting post proposal re-runner with ChatGPT oversight")
    process_all_proposals()
    logger.info("Post proposal re-runner with ChatGPT oversight finished")


if __name__ == "__main__":
    main()
