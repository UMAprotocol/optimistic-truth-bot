#!/usr/bin/env python3
"""
UMA Proposal Replayer - Monitors proposals directory, queries Perplexity API for solutions, saves outputs.
Usage: python proposal_replayer/proposal_replayer.py [--start-block NUMBER] [--output-dir PATH]
"""

import os, json, time, threading, sys
import argparse
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Parse command line arguments
parser = argparse.ArgumentParser(description="UMA Proposal Replayer")
parser.add_argument(
    "--start-block",
    type=int,
    default=0,
    help="Starting block number to process proposals from",
)
parser.add_argument("--output-dir", type=str, help="Directory to store output files")
args = parser.parse_args()

print(
    "🔍 Starting UMA Proposal Replayer - Monitoring for proposals and querying Perplexity API 🤖 📊"
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import (
    setup_logging,
    query_perplexity,
    extract_recommendation,
    spinner_animation,
)
from prompt import get_system_prompt

logger = setup_logging("proposal_monitor", "logs/proposal_monitor.log")
load_dotenv()
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

PROPOSALS_DIR = Path(__file__).parent / "proposals"
# Use command line argument for output directory if provided, otherwise use default
OUTPUTS_DIR = (
    Path(args.output_dir) if args.output_dir else Path(__file__).parent / "outputs"
)
OUTPUTS_DIR.mkdir(exist_ok=True)

# Store the starting block number
START_BLOCK_NUMBER = args.start_block

logger.info(f"Using starting block number: {START_BLOCK_NUMBER}")
logger.info(f"Output directory set to: {OUTPUTS_DIR}")


def format_prompt_from_json(proposal_data):
    if isinstance(proposal_data, list) and len(proposal_data) > 0:
        proposal_data = proposal_data[0]

    ancillary_data = proposal_data.get("ancillary_data", "")
    resolution_conditions = proposal_data.get("resolution_conditions", "")
    updates = proposal_data.get("updates", [])

    prompt = f"system: {get_system_prompt()}\n\n"
    prompt += f"user:\n\nancillary_data:\n{ancillary_data}\n\n"
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
    return f"output_{get_question_id_short(query_id)}.json"


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
            return True

        query_id = get_query_id_from_proposal(proposal_data)
        if query_id and is_already_processed(query_id):
            logger.info(f"Proposal {query_id} already processed, skipping")
            return True

        prompt_content = format_prompt_from_json(proposal_data)

        is_list = isinstance(proposal_data, list) and len(proposal_data) > 0
        tx_hash = (proposal_data[0] if is_list else proposal_data).get(
            "transaction_hash", ""
        )
        price = (proposal_data[0] if is_list else proposal_data).get(
            "proposed_price", None
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

        output_file = OUTPUTS_DIR / get_output_filename(query_id)
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        logger.info(
            f"Output saved to {output_file} with recommendation: {output_data['recommendation']}"
        )
        return True

    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        return False


def process_all_existing_files():
    logger.info(
        f"Checking for unprocessed files in proposals directory (block >= {START_BLOCK_NUMBER})"
    )

    for file_path in PROPOSALS_DIR.glob("*.json"):
        try:
            with open(file_path, "r") as f:
                proposal_data = json.load(f)

            # Check if the proposal meets our block number requirement
            if not should_process_proposal(proposal_data):
                logger.debug(
                    f"Skipping {file_path.name} with block number below {START_BLOCK_NUMBER}"
                )
                continue

            query_id = get_query_id_from_proposal(proposal_data)

            if not is_already_processed(query_id):
                logger.info(f"Found unprocessed file: {file_path.name}")
                process_proposal_file(file_path)
            else:
                logger.debug(f"Skipping already processed file: {file_path.name}")
        except Exception as e:
            logger.error(f"Error checking file {file_path}: {str(e)}")


class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".json"):
            logger.info(f"New proposal detected: {os.path.basename(event.src_path)}")
            time.sleep(1)  # Small delay to ensure file is fully written
            process_proposal_file(event.src_path)


def main():
    logger.info("Starting proposal monitor")
    process_all_existing_files()

    observer = Observer()
    observer.schedule(NewFileHandler(), str(PROPOSALS_DIR), recursive=False)
    observer.start()
    logger.info(f"Watching directory: {PROPOSALS_DIR}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping monitor due to keyboard interrupt")
        observer.stop()

    observer.join()
    logger.info("Proposal monitor stopped")


if __name__ == "__main__":
    main()
