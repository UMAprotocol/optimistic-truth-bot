#!/usr/bin/env python3
"""
UMA Proposal Finalizer - Checks unresolved proposals/outputs and updates them with
the final resolution prices from the blockchain.

Usage: python proposal_replayer/proposal_finalizer.py [--continuous] [--interval SECONDS]
"""

import os
import json
import sys
import glob
import time
import argparse
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

# Add the parent directory to the path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
from common import (
    load_abi,
    OptimisticOracleV2,
    UmaCtfAdapter,
    yesOrNoIdentifier,
    setup_logging,
    price_to_outcome,
)

# Load .env file from project root
dotenv_path = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path)

# Setup logging
logger = setup_logging("proposal_finalizer", "logs/proposal_finalizer.log")

# Directory paths
CURRENT_DIR = Path(__file__).parent
OUTPUTS_DIR = CURRENT_DIR / "outputs"

logger.info(f"Outputs directory: {OUTPUTS_DIR}")

# Set up Web3 connection
POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL")
if not POLYGON_RPC_URL:
    logger.error("POLYGON_RPC_URL not found in environment variables")
    sys.exit(1)

logger.info(f"Using Polygon RPC URL: {POLYGON_RPC_URL}")

w3 = Web3(Web3.HTTPProvider(POLYGON_RPC_URL))
if not w3.is_connected():
    logger.error("Failed to connect to Polygon network")
    sys.exit(1)

logger.info(f"Connected to Polygon network: {w3.is_connected()}")

# Initialize contract
try:
    oov2_contract = w3.eth.contract(
        address=OptimisticOracleV2, abi=load_abi("OptimisticOracleV2.json")
    )
    logger.info("Contracts initialized successfully")
except Exception as e:
    logger.error(f"Error initializing contracts: {str(e)}")
    sys.exit(1)


def get_market_resolution(output_data):
    query_id = output_data.get("query_id")
    if not query_id:
        logger.warning("No query_id found in output data")
        return None

    logger.info(f"Checking resolution for query ID: {query_id}")

    # Get metadata from the output file
    metadata = output_data.get("proposal_metadata")
    if not metadata:
        metadata = output_data.get("raw_proposal_data", [{}])[0]
        if not metadata:
            logger.warning(f"No metadata found for {query_id}")
            return None

    # Extract required data from metadata
    timestamp = metadata.get("unix_timestamp")
    ancillary_data_hex = metadata.get("ancillary_data_hex")

    if not timestamp or not ancillary_data_hex:
        logger.warning(f"Missing timestamp or ancillary data for {query_id}")
        return None

    try:
        # Query OOV2 for request details directly
        request_data = oov2_contract.functions.getRequest(
            UmaCtfAdapter, yesOrNoIdentifier, timestamp, ancillary_data_hex
        ).call()

        # Return partial data even if market is not settled
        disputer_address = request_data[1]
        resolved_price = (
            request_data[6] if request_data[3] else None
        )  # Only include price if settled
        is_settled = request_data[3]  # settled flag

        logger.info(f"Market {query_id} disputer address: {disputer_address}")
        if is_settled:
            logger.info(f"Market {query_id} resolved with price: {resolved_price}")
        else:
            logger.info(f"Market {query_id} not settled yet")

        return {
            "resolved_price": resolved_price,
            "disputer_address": disputer_address,
            "is_settled": is_settled,
        }

    except Exception as e:
        logger.error(f"Error querying resolution for {query_id}: {str(e)}")
        return None


def update_output_file(output_path, resolution_data):
    try:
        if not resolution_data:
            logger.error(f"No resolution data provided for {output_path}")
            return False

        with open(output_path, "r") as f:
            data = json.load(f)

        # Add proposed_price_outcome using the proposed_price if it exists
        if "proposed_price" in data:
            data["proposed_price_outcome"] = price_to_outcome(data["proposed_price"])

        # Add dispute information
        zero_address = "0x0000000000000000000000000000000000000000"
        disputer_address = resolution_data.get("disputer_address")
        is_disputed = disputer_address != zero_address
        data["disputed"] = is_disputed

        if is_disputed:
            data["disputer_address"] = disputer_address
            logger.info(
                f"Market {data.get('query_id')} was disputed by {disputer_address}"
            )

        # Update resolved price if the market is settled
        if resolution_data.get("is_settled"):
            data["resolved_price"] = resolution_data.get("resolved_price")
            data["resolved_price_outcome"] = price_to_outcome(
                resolution_data.get("resolved_price")
            )
        else:
            # For unsettled markets, set resolved_price_outcome to null
            data["resolved_price_outcome"] = None

        # Restructure raw_proposal_data to proposal_metadata
        if "raw_proposal_data" in data:
            raw_data = data.pop("raw_proposal_data")
            if isinstance(raw_data, list) and len(raw_data) > 0:
                raw_data = raw_data[0]

            # Create a cleaner proposal_metadata structure
            data["proposal_metadata"] = {
                "creator": raw_data.get("creator", ""),
                "proposal_bond": raw_data.get("proposal_bond", 0),
                "reward_amount": raw_data.get("reward_amount", 0),
                "unix_timestamp": raw_data.get("unix_timestamp", 0),
                "block_number": raw_data.get("block_number", 0),
                "updates": raw_data.get("updates", []),
                "ancillary_data_hex": raw_data.get("ancillary_data_hex", ""),
            }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Updated {output_path.name} with additional information")
        return True
    except Exception as e:
        logger.error(f"Error updating file {output_path}: {str(e)}")
        return False


def process_files(directory, file_type):
    """Process all JSON files in the specified directory and update unresolved ones."""
    logger.info(f"Starting to process {file_type} files in {directory}")

    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return 0, 0, 0, 0

    processed_count = 0
    updated_count = 0
    error_count = 0
    skipped_count = 0

    for file_path in directory.glob("*.json"):
        processed_count += 1

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            # Skip if already resolved
            if data.get("resolved_price") is not None:
                logger.debug(f"Skipping already resolved file: {file_path.name}")
                skipped_count += 1
                continue

            # Query blockchain for resolution using the data
            resolution_data = get_market_resolution(data)

            if resolution_data is not None:
                # Update the file with resolution data (partial or complete)
                if update_output_file(file_path, resolution_data):
                    updated_count += 1
                else:
                    error_count += 1
            else:
                logger.info(
                    f"Could not retrieve data for {data.get('query_id')}, skipping"
                )
                skipped_count += 1

        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {str(e)}")
            error_count += 1

    logger.info(
        f"{file_type} processing complete. Processed: {processed_count}, Updated: {updated_count}, Errors: {error_count}, Skipped: {skipped_count}"
    )

    return processed_count, updated_count, error_count, skipped_count


def process_all_results_directories():
    """Process all experiment directories in the results folder."""
    results_dir = Path(__file__).parent / "results"

    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}")
        return

    # Find all experiment directories in results folder
    experiment_dirs = [
        d for d in results_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
    ]

    if not experiment_dirs:
        print("No experiment directories found in results folder")
        return

    for exp_dir in experiment_dirs:
        print(f"\n🔍 Processing experiment directory: {exp_dir.name}")

        # Look for outputs directory in each experiment folder
        outputs_dir = exp_dir / "outputs"
        if not outputs_dir.exists() or not outputs_dir.is_dir():
            print(f"  ⚠️ No outputs directory found in {exp_dir.name}, skipping...")
            continue

        # Process all JSON files in the outputs directory
        file_count = len(list(outputs_dir.glob("*.json")))
        if file_count == 0:
            print(f"  ⚠️ No JSON files found in {exp_dir.name}/outputs, skipping...")
            continue

        print(f"  📊 Found {file_count} files in {exp_dir.name}/outputs")

        # Process the files
        processed, updated, errors, skipped = process_files(outputs_dir, "outputs")
        print(
            f"  ✅ Processed: {processed}, Updated: {updated}, Errors: {errors}, Skipped: {skipped}"
        )


def main():
    parser = argparse.ArgumentParser(description="UMA Proposal Finalizer")
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run in continuous mode, rechecking proposals periodically",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Interval in seconds between rechecks (default: 30)",
    )
    args = parser.parse_args()

    logger.info(
        "🔍 Starting UMA Proposal Finalizer - Updating unresolved markets with blockchain data 🔄"
    )

    try:
        if args.continuous:
            logger.info(
                f"Running in continuous mode. Will recheck every {args.interval} seconds. Press Ctrl+C to exit."
            )
            while True:
                # Process all results directories
                process_all_results_directories()
                logger.info(f"Waiting {args.interval} seconds before next check...")
                time.sleep(args.interval)
        else:
            # Process all results directories once
            process_all_results_directories()
            logger.info("✅ Proposal finalizer completed")
    except KeyboardInterrupt:
        logger.info("🛑 Proposal finalizer stopped by user")
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")


if __name__ == "__main__":
    main()
