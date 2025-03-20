#!/usr/bin/env python3
"""
UMA Proposal Replayer with ChatGPT Oversight - Monitors proposals directory, queries Perplexity API with ChatGPT validation.
Usage: python proposal_overseer/proposal_replayer.py [--start-block NUMBER] [--output-dir PATH] [--max-attempts NUMBER]
"""

import os
import json
import time
import sys
import argparse
import re
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Parse command line arguments
parser = argparse.ArgumentParser(
    description="UMA Proposal Replayer with ChatGPT Oversight"
)
parser.add_argument(
    "--start-block",
    type=int,
    default=0,
    help="Starting block number to process proposals from",
)
parser.add_argument("--output-dir", type=str, help="Directory to store output files")
parser.add_argument(
    "--proposals-dir",
    type=str,
    help="Directory containing proposal JSON files to process",
)
parser.add_argument(
    "--max-attempts",
    type=int,
    default=3,
    help="Maximum number of attempts to query Perplexity with ChatGPT validation",
)
parser.add_argument(
    "--min-attempts",
    type=int,
    default=2,
    help="Minimum number of attempts before defaulting to p4",
)
args = parser.parse_args()

print(
    "🔍 Starting UMA Proposal Replayer with ChatGPT Oversight - Monitoring for proposals and validating results 🤖 📊"
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

logger = setup_logging("proposal_overseer", "logs/proposal_overseer.log")
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

logger.info(f"Using starting block number: {START_BLOCK_NUMBER}")
logger.info(f"Proposals directory set to: {PROPOSALS_DIR}")
logger.info(f"Output directory set to: {OUTPUTS_DIR}")
logger.info(f"Maximum attempts set to: {MAX_ATTEMPTS}")
logger.info(f"Minimum attempts before defaulting to p4: {MIN_ATTEMPTS}")


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
            return True

        query_id = get_query_id_from_proposal(proposal_data)
        if query_id and is_already_processed(query_id):
            logger.info(f"Proposal {query_id} already processed, skipping")
            return True

        user_prompt = format_prompt_from_json(proposal_data)
        system_prompt = get_system_prompt()

        is_list = isinstance(proposal_data, list) and len(proposal_data) > 0
        tx_hash = (proposal_data[0] if is_list else proposal_data).get(
            "transaction_hash", ""
        )
        price = (proposal_data[0] if is_list else proposal_data).get(
            "proposed_price", None
        )

        logger.info(
            f"Starting enhanced Perplexity-ChatGPT loop for {get_question_id_short(query_id)}"
        )

        result = enhanced_perplexity_chatgpt_loop(
            user_prompt=user_prompt,
            perplexity_api_key=PERPLEXITY_API_KEY,
            chatgpt_api_key=OPENAI_API_KEY,
            original_system_prompt=system_prompt,
            logger=logger,
            max_attempts=MAX_ATTEMPTS,
            min_attempts=MIN_ATTEMPTS,
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
            "initial_recommendation": result["initial_recommendation"],
            "recommendation": result["final_recommendation"],
            "recommendation_changed": result["recommendation_changed"],
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
    logger.info("Starting proposal monitor with ChatGPT oversight")
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
