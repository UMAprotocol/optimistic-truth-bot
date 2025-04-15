#!/usr/bin/env python3
"""
UMA Post Proposal Re-runner - Processes existing proposals older than 2 hours, queries Perplexity API for solutions.
Usage: python proposal_replayer/post_proposal_rerunner.py [--proposals_dir PATH] [--output_dir PATH] [--max_concurrent N]
"""

import os, json, time, threading, sys, argparse, queue
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from collections import deque
from concurrent.futures import ThreadPoolExecutor

print(
    "🔍 Starting UMA Post Proposal Re-runner - Processing existing proposals older than 2 hours 🤖 📊"
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import (
    setup_logging,
    query_perplexity,
    extract_recommendation,
    spinner_animation,
)
from prompt import get_system_prompt

logger = setup_logging("post_proposal_rerunner", "logs/post_proposal_rerunner.log")
load_dotenv()
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")


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


def parse_arguments():
    parser = argparse.ArgumentParser(description="UMA Post Proposal Re-runner")
    parser.add_argument(
        "--proposals_dir",
        type=str,
        default=str(Path(__file__).parent / "proposals"),
        help="Directory containing proposal files",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(Path(__file__).parent / "reruns"),
        help="Directory to save rerun outputs",
    )
    parser.add_argument(
        "--max_concurrent",
        type=int,
        default=5,
        help="Maximum number of concurrent API requests",
    )
    return parser.parse_args()


def format_prompt_from_json(proposal_data):
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
    if isinstance(proposal_data, list) and len(proposal_data) > 0:
        return proposal_data[0].get("query_id", "")
    return proposal_data.get("query_id", "")


def get_question_id_short(query_id):
    if not query_id:
        return "unknown"
    return query_id[2:10] if query_id.startswith("0x") else query_id[:8]


def get_output_filename(query_id):
    return f"{get_question_id_short(query_id)}.json"


def is_already_processed(query_id, output_dir):
    if not query_id:
        return False
    return (Path(output_dir) / get_output_filename(query_id)).exists()


def is_older_than_two_hours(unix_timestamp):
    current_time = int(time.time())
    return (current_time - unix_timestamp) > (2 * 60 * 60)  # 2 hours in seconds


def process_proposal_file(file_path, output_dir):
    file_name = os.path.basename(file_path)
    logger.info(f"Processing proposal: {file_name}")

    try:
        with open(file_path, "r") as f:
            proposal_data = json.load(f)

        query_id = get_query_id_from_proposal(proposal_data)
        if query_id and is_already_processed(query_id, output_dir):
            logger.info(f"Proposal {query_id} already processed, skipping")
            return True, False  # Processed, but no API call made

        # Get timestamp and check if older than 2 hours
        if isinstance(proposal_data, list) and len(proposal_data) > 0:
            unix_timestamp = proposal_data[0].get("unix_timestamp", 0)
        else:
            unix_timestamp = proposal_data.get("unix_timestamp", 0)

        if not is_older_than_two_hours(unix_timestamp):
            logger.info(f"Proposal {query_id} is less than 2 hours old, skipping")
            return False, False  # Not processed, no API call made

        prompt_content = format_prompt_from_json(proposal_data)

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
            f"Starting API request for {get_question_id_short(query_id)} (in-flight: {in_flight})"
        )

        start_time = time.time()
        stop_spinner = threading.Event()
        spinner_thread = threading.Thread(
            target=spinner_animation,
            args=(
                stop_spinner,
                f"Querying Perplexity API for {get_question_id_short(query_id)}",
            ),
            daemon=True,
        )
        spinner_thread.start()

        try:
            response = query_perplexity(
                prompt_content, PERPLEXITY_API_KEY, verbose=False
            )
        finally:
            stop_spinner.set()
            spinner_thread.join()
            # Decrement in-flight counter
            in_flight = perplexity_rate_limiter.decrement_in_flight()
            logger.info(
                f"Completed API request for {get_question_id_short(query_id)} (in-flight: {in_flight})"
            )

        api_response_time = time.time() - start_time
        logger.info(f"API response received in {api_response_time:.2f} seconds")

        response_text = response.choices[0].message.content
        citations = (
            [citation for citation in response.citations]
            if hasattr(response, "citations")
            else []
        )

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
            "transaction_hash": raw_data.get("transaction_hash", ""),
            "request_transaction_block_time": raw_data.get("request_transaction_block_time", ""),
            "request_timestamp": raw_data.get("request_timestamp", 0),
            "expiration_timestamp": raw_data.get("expiration_timestamp", 0),
            "proposer": raw_data.get("proposer", ""),
            "bond_currency": raw_data.get("bond_currency", ""),
            "condition_id": raw_data.get("condition_id", "")
        }

        output_data = {
            "query_id": query_id,
            "question_id_short": get_question_id_short(query_id),
            "transaction_hash": tx_hash,
            "user_prompt": prompt_content,
            "system_prompt": get_system_prompt(),
            "response": response_text,
            "recommendation": extract_recommendation(response_text),
            "proposed_price": price,
            "resolved_price": None,
            "timestamp": time.time(),
            "processed_file": file_name,
            "resolved_price_outcome": None,
            "disputed": False,
            "recommendation_overridden": False,
            "proposed_price_outcome": extract_recommendation(response_text),
            "response_metadata": {
                "model": response.model,
                "created_timestamp": response.created,
                "created_datetime": datetime.fromtimestamp(
                    response.created
                ).isoformat(),
                "completion_tokens": response.usage.completion_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "total_tokens": response.usage.total_tokens,
                "api_response_time_seconds": api_response_time,
            },
            "citations": citations,
            "proposal_metadata": proposal_metadata,
        }

        # Include tags if they exist in the proposal data
        if "tags" in raw_data:
            output_data["tags"] = raw_data.get("tags", [])

        output_file = Path(output_dir) / get_output_filename(query_id)
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        logger.info(
            f"Output saved to {output_file} with recommendation: {output_data['recommendation']}"
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


def process_all_proposals(proposals_dir, output_dir, max_concurrent):
    logger.info(f"Processing all proposals older than 2 hours from {proposals_dir}")
    logger.info(f"Using maximum of {max_concurrent} concurrent requests")
    Path(output_dir).mkdir(exist_ok=True)

    # Collect all proposal files first
    proposal_files = list(Path(proposals_dir).glob("*.json"))
    logger.info(f"Found {len(proposal_files)} proposal files to process")

    # Setup counters
    processed_count = 0
    skipped_count = 0
    api_calls_made = 0
    start_time = time.time()

    # Process files with a thread pool
    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(process_proposal_file, file_path, output_dir): file_path
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
    args = parse_arguments()
    logger.info("Starting post proposal re-runner")
    process_all_proposals(args.proposals_dir, args.output_dir, args.max_concurrent)
    logger.info("Post proposal re-runner finished")


if __name__ == "__main__":
    main()
