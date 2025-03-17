#!/usr/bin/env python3
"""
Market categorizer that fetches tags from Polymarket API using computed condition IDs.
"""

import json
import os
import sys
from pathlib import Path
import time
import requests
from web3 import Web3
from dotenv import load_dotenv
import itertools
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import UmaCtfAdapter, setup_logging, spinner_animation
import threading

load_dotenv()

logger = setup_logging("market_categorizer", "market_categorizer.log")
POLYMARKET_API_BASE = "https://clob.polymarket.com/markets/"
MIN_REQUEST_INTERVAL = 0.5  # 500ms between API requests

# Directory paths
CURRENT_DIR = Path(__file__).parent
PROPOSALS_DIR = CURRENT_DIR / "proposals"


def compute_condition_id(
    oracle_address: str, question_id: str, outcome_slot_count: int
) -> str:
    oracle_address = Web3.to_checksum_address(oracle_address)
    # Pack the parameters as in Solidity
    packed = Web3.solidity_keccak(
        ["address", "bytes32", "uint256"],
        [oracle_address, question_id, outcome_slot_count],
    )

    return "0x" + packed.hex()


def get_polymarket_data(condition_id: str) -> dict:
    """Fetch market data from Polymarket API with rate limiting."""
    url = f"{POLYMARKET_API_BASE}{condition_id}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Polymarket data for {condition_id}: {str(e)}")
        return None
    finally:
        time.sleep(MIN_REQUEST_INTERVAL)


def process_single_proposal(proposal_file: Path) -> bool:
    """Process a single proposal file and update with Polymarket tags."""
    try:
        with open(proposal_file, "r") as f:
            data = json.load(f)

        if isinstance(data, list) and len(data) > 0:
            data = data[0]

        # Skip if already has tags
        if "tags" in data:
            return False

        question_id = data.get("query_id")
        if not question_id:
            logger.error(f"No query_id found in {proposal_file.name}")
            return False

        # Compute condition ID
        condition_id = compute_condition_id(UmaCtfAdapter, question_id, 2)

        # Fetch Polymarket data
        poly_data = get_polymarket_data(condition_id)
        if not poly_data:
            return False

        # Extract tags
        tags = poly_data.get("tags", [])

        # Update the data
        data["tags"] = tags

        # Save back to file
        with open(proposal_file, "w") as f:
            json.dump([data], f, indent=2)

        return True

    except Exception as e:
        logger.error(f"Error processing {proposal_file.name}: {str(e)}")
        return False


def process_proposals():
    """Process all proposal files and add Polymarket tags."""
    proposal_files = list(PROPOSALS_DIR.glob("questionId_*.json"))
    total_files = len(proposal_files)
    processed = 0

    print(f"\nFound {total_files} proposal files to process")
    print("\nProcessing files:")
    print("=" * 80)

    try:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(process_single_proposal, proposal_file)
                for proposal_file in proposal_files
            ]

            # Monitor progress with progress bar
            for future in concurrent.futures.as_completed(futures):
                if future.result():  # Only increment if processing was successful
                    processed += 1

                # Update progress bar
                progress = int(50 * processed / total_files)
                sys.stdout.write(
                    f"\r[{'=' * progress}{' ' * (50 - progress)}] {processed}/{total_files} ({processed/total_files:.1%})"
                )
                sys.stdout.flush()

    finally:
        print("\n")  # New line after progress bar

    print(f"Completed processing {processed} files")
    logger.info(f"Completed processing {processed} files")


if __name__ == "__main__":
    process_proposals()
