#!/usr/bin/env python3
"""
UMA Post Proposal Re-runner - Processes existing proposals older than 2 hours, queries Perplexity API for solutions.
Usage: python proposal_replayer/post_proposal_rerunner.py
"""

import os, json, time, threading, sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

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

PROPOSALS_DIR = Path(__file__).parent / "proposals"
RERUN_DIR = Path(__file__).parent / "reruns"
RERUN_DIR.mkdir(exist_ok=True)


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
    return f"rerun_{get_question_id_short(query_id)}.json"


def is_already_processed(query_id):
    if not query_id:
        return False
    return (RERUN_DIR / get_output_filename(query_id)).exists()


def is_older_than_two_hours(unix_timestamp):
    current_time = int(time.time())
    return (current_time - unix_timestamp) > (2 * 60 * 60)  # 2 hours in seconds


def process_proposal_file(file_path):
    file_name = os.path.basename(file_path)
    logger.info(f"Processing proposal: {file_name}")

    try:
        with open(file_path, "r") as f:
            proposal_data = json.load(f)

        query_id = get_query_id_from_proposal(proposal_data)
        if query_id and is_already_processed(query_id):
            logger.info(f"Proposal {query_id} already processed, skipping")
            return True

        # Get timestamp and check if older than 2 hours
        if isinstance(proposal_data, list) and len(proposal_data) > 0:
            unix_timestamp = proposal_data[0].get("unix_timestamp", 0)
        else:
            unix_timestamp = proposal_data.get("unix_timestamp", 0)

        if not is_older_than_two_hours(unix_timestamp):
            logger.info(f"Proposal {query_id} is less than 2 hours old, skipping")
            return False

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

        output_file = RERUN_DIR / get_output_filename(query_id)
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        logger.info(
            f"Output saved to {output_file} with recommendation: {output_data['recommendation']}"
        )
        return True

    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        return False


def process_all_proposals():
    logger.info("Processing all proposals older than 2 hours")
    processed_count = 0
    skipped_count = 0

    for file_path in PROPOSALS_DIR.glob("*.json"):
        try:
            if process_proposal_file(file_path):
                processed_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            skipped_count += 1

    logger.info(
        f"Processing complete. Processed: {processed_count}, Skipped: {skipped_count}"
    )


def main():
    logger.info("Starting post proposal re-runner")
    process_all_proposals()
    logger.info("Post proposal re-runner finished")


if __name__ == "__main__":
    main()
