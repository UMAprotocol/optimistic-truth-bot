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
    spinner,
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


def is_valid_proposal_file(proposal_data):
    """Check if the JSON data is a valid proposal file with required fields."""
    # If it's a list, check the first item
    if isinstance(proposal_data, list):
        if not proposal_data:  # Empty list
            return False
        proposal_data = proposal_data[0]

    # Check for required fields that all proposal files should have
    required_fields = ["query_id", "ancillary_data"]
    for field in required_fields:
        if field not in proposal_data:
            return False

    # Additional validation: ensure it's not a metadata file
    if (
        proposal_data.get("title")
        and proposal_data.get("description")
        and "dataset" in proposal_data.get("description", "").lower()
    ):
        return False

    return True


def process_proposal_file(file_path):
    file_name = os.path.basename(file_path)
    logger.info(f"Processing proposal: {file_name}")

    try:
        with open(file_path, "r") as f:
            proposal_data = json.load(f)

        # Validate if this is a properly formatted proposal file
        if not is_valid_proposal_file(proposal_data):
            logger.info(f"Skipping {file_name} - not a valid proposal file format")
            return True

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

        try:
            result = enhanced_perplexity_chatgpt_loop(
                user_prompt=user_prompt,
                perplexity_api_key=PERPLEXITY_API_KEY,
                chatgpt_api_key=OPENAI_API_KEY,
                original_system_prompt=system_prompt,
                logger=logger,
                max_attempts=MAX_ATTEMPTS,
                min_attempts=MIN_ATTEMPTS,
            )

            # Verify we have valid Perplexity responses before proceeding
            perplexity_responses = [
                r
                for r in result.get("responses", [])
                if r.get("interaction_type") == "perplexity_query"
            ]
            if not perplexity_responses:
                error_msg = f"No valid Perplexity responses for {get_question_id_short(query_id)}"
                logger.error(error_msg)
                return False  # Don't proceed with ChatGPT or save output

            # Verify result has valid data structure before continuing
            if not result.get("final_recommendation") or not result.get(
                "final_response"
            ):
                error_msg = f"Invalid result format from API calls for {get_question_id_short(query_id)}"
                logger.error(error_msg)
                return False  # Don't save invalid results
        except Exception as e:
            # Clean up error message if it contains HTML
            error_msg = str(e)
            if len(error_msg) > 100 and ("<html>" in error_msg or "401" in error_msg):
                error_msg = f"Perplexity API authentication error (401 Unauthorized) for {get_question_id_short(query_id)}"
            else:
                error_msg = f"Error in Perplexity-ChatGPT loop for {get_question_id_short(query_id)}: {error_msg}"

            logger.error(error_msg)
            return False  # Exit this proposal processing but continue with others

        # Extract and organize proposal metadata
        if isinstance(proposal_data, list) and len(proposal_data) > 0:
            raw_data = proposal_data[0]
        else:
            raw_data = proposal_data

        # Extract all fields from the original proposal to ensure we save everything
        proposal_metadata = {k: v for k, v in raw_data.items() if k not in [
            "query_id",  # These fields are already at the top level
            "transaction_hash", 
            "proposed_price",
            "ancillary_data",
            "resolution_conditions",
            "updates",
            "tags"
        ]}

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
            # Skip metadata files
            if file_path.name.lower() == "metadata.json":
                logger.info(f"Skipping metadata file: {file_path.name}")
                continue

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
            file_name = os.path.basename(event.src_path)

            # Skip metadata files
            if file_name.lower() == "metadata.json":
                logger.info(f"Skipping metadata file: {file_name}")
                return

            logger.info(f"New proposal detected: {file_name}")
            time.sleep(1)  # Small delay to ensure file is fully written
            process_proposal_file(event.src_path)


def main():
    logger.info("Starting proposal monitor with ChatGPT oversight")

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
        # Check for a valid response object with expected attributes
        if (
            not test_result
            or not hasattr(test_result, "choices")
            or not test_result.choices
        ):
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
