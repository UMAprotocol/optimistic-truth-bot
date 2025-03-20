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
args = parser.parse_args()

print(
    "🔍 Starting UMA Post Proposal Re-runner with ChatGPT Oversight - Processing existing proposals 🤖 📊"
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompt import get_system_prompt

# Import locally defined modules
from proposal_overseer.common import (
    setup_logging,
    spinner_animation,
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

logger.info(f"Using starting block number: {START_BLOCK_NUMBER}")
logger.info(f"Proposals directory set to: {PROPOSALS_DIR}")
logger.info(f"Output directory set to: {OUTPUTS_DIR}")
logger.info(f"Maximum attempts set to: {MAX_ATTEMPTS}")
logger.info(f"Minimum attempts before defaulting to p4: {MIN_ATTEMPTS}")
logger.info(f"Maximum concurrent requests set to: {MAX_CONCURRENT}")


class RateLimiter:
    """Rate limiter for API calls with a maximum of N requests per minute."""

    def __init__(self, max_requests_per_minute=5):
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
                    f"Rate limit reached. Waiting {wait_time:.2f} seconds before next request"
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


# Create a global rate limiter instance
perplexity_rate_limiter = RateLimiter(max_requests_per_minute=5)


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


def process_proposal_file(file_path):
    file_name = os.path.basename(file_path)
    logger.info(f"Processing proposal: {file_name}")

    try:
        with open(file_path, "r") as f:
            proposal_data = json.load(f)

        # Check if we should process this proposal based on block number
        if not should_process_proposal(proposal_data):
            logger.info(
                f"Skipping proposal with block number below {START_BLOCK_NUMBER}"
            )
            return True, False  # Processed (skipped), but no API call made

        query_id = get_query_id_from_proposal(proposal_data)
        if query_id and is_already_processed(query_id):
            logger.info(f"Proposal {query_id} already processed, skipping")
            return True, False  # Processed (skipped), but no API call made

        user_prompt = format_prompt_from_json(proposal_data)
        system_prompt = get_system_prompt()

        is_list = isinstance(proposal_data, list) and len(proposal_data) > 0
        tx_hash = (proposal_data[0] if is_list else proposal_data).get(
            "transaction_hash", ""
        )
        price = (proposal_data[0] if is_list else proposal_data).get(
            "proposed_price", None
        )

        # Wait if needed to respect rate limits
        wait_time = perplexity_rate_limiter.wait_if_needed()
        if wait_time > 0:
            logger.info(
                f"Rate limited: waited {wait_time:.2f}s before querying for {get_question_id_short(query_id)}"
            )

        # Track in-flight requests
        in_flight = perplexity_rate_limiter.increment_in_flight()
        logger.info(
            f"Starting Perplexity-ChatGPT loop for {get_question_id_short(query_id)} (in-flight: {in_flight})"
        )

        start_time = time.time()
        try:
            # Use the enhanced loop function that enforces minimum attempts
            result = enhanced_perplexity_chatgpt_loop(
                user_prompt=user_prompt,
                perplexity_api_key=PERPLEXITY_API_KEY,
                chatgpt_api_key=OPENAI_API_KEY,
                original_system_prompt=system_prompt,
                logger=logger,
                max_attempts=MAX_ATTEMPTS,
                min_attempts=MIN_ATTEMPTS,
            )
        finally:
            # Decrement in-flight counter
            in_flight = perplexity_rate_limiter.decrement_in_flight()
            logger.info(
                f"Completed Perplexity-ChatGPT loop for {get_question_id_short(query_id)} (in-flight: {in_flight})"
            )

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

        logger.info(
            f"Output saved to {output_file} with final recommendation: {output_data['recommendation']}"
        )
        return True, True  # Processed and API call made

    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        # Ensure we decrement in-flight counter even on error
        try:
            perplexity_rate_limiter.decrement_in_flight()
        except:
            pass
        return False, False  # Not processed, no API call made


def process_all_proposals():
    logger.info(f"Processing all proposals from {PROPOSALS_DIR}")
    logger.info(f"Using maximum of {MAX_CONCURRENT} concurrent requests")

    # Collect all proposal files first
    proposal_files = list(Path(PROPOSALS_DIR).glob("*.json"))
    logger.info(f"Found {len(proposal_files)} proposal files to process")

    # Setup counters
    processed_count = 0
    skipped_count = 0
    api_calls_made = 0
    start_time = time.time()

    # Process files with a thread pool
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(process_proposal_file, file_path): file_path
            for file_path in proposal_files
        }

        # Process results as they complete
        for future in future_to_file:
            file_path = future_to_file[future]
            try:
                processed, api_call_made = future.result()
                if processed:
                    processed_count += 1
                    if api_call_made:
                        api_calls_made += 1
                else:
                    skipped_count += 1
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")
                skipped_count += 1

    elapsed_time = time.time() - start_time
    runtime_minutes = elapsed_time / 60

    logger.info(
        f"Processing complete. Processed: {processed_count}, Skipped: {skipped_count}"
    )
    logger.info(
        f"API usage summary: {api_calls_made} calls over {runtime_minutes:.2f} minutes "
        f"(Average: {api_calls_made/max(1, runtime_minutes):.2f} calls/minute)"
    )


def main():
    logger.info("Starting post proposal re-runner with ChatGPT oversight")
    process_all_proposals()
    logger.info("Post proposal re-runner with ChatGPT oversight finished")


if __name__ == "__main__":
    main()
