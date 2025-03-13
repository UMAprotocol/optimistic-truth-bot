#!/usr/bin/env python3
"""
UMA Proposal Finalizer - Checks unresolved proposals/outputs and updates them with
the final resolution prices from the blockchain.

Usage: python proposal_replayer/proposal_finalizer.py
"""

import os
import json
import sys
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import (
    load_abi,
    OptimisticOracleV2,
    UmaCtfAdapter,
    yesOrNoIdentifier,
    setup_logging,
    price_to_outcome,
)

# Setup logging
logger = setup_logging("proposal_finalizer", "logs/proposal_finalizer.log")
load_dotenv()

# Directory paths
CURRENT_DIR = Path(__file__).parent
OUTPUTS_DIR = CURRENT_DIR / "outputs"

logger.info(f"Outputs directory: {OUTPUTS_DIR}")

# Set up Web3 connection
POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL")
if not POLYGON_RPC_URL:
    logger.error("POLYGON_RPC_URL not found in environment variables")
    sys.exit(1)

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

        # Check if market has settled
        if not request_data[3]:  # settled flag
            logger.info(f"Market {query_id} not settled yet")
            return None
        resolved_price = request_data[6]

        logger.info(f"Market {query_id} resolved with price: {resolved_price}")
        return resolved_price

    except Exception as e:
        logger.error(f"Error querying resolution for {query_id}: {str(e)}")
        return None


def update_output_file(output_path, resolved_price):
    try:
        with open(output_path, "r") as f:
            data = json.load(f)

        # Update the resolved price
        data["resolved_price"] = resolved_price
        data["resolved_price_outcome"] = price_to_outcome(resolved_price)

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

        logger.info(f"Updated {output_path.name} with resolved price: {resolved_price}")
        return True
    except Exception as e:
        logger.error(f"Error updating file {output_path}: {str(e)}")
        return False


def process_outputs():
    """Process all output files and update unresolved ones."""
    logger.info("Starting to process output files")

    if not OUTPUTS_DIR.exists():
        logger.error(f"Outputs directory not found: {OUTPUTS_DIR}")
        return

    processed_count = 0
    updated_count = 0
    error_count = 0
    skipped_count = 0

    for output_file in OUTPUTS_DIR.glob("*.json"):
        processed_count += 1

        try:
            with open(output_file, "r") as f:
                data = json.load(f)

            # Skip if already resolved
            if data.get("resolved_price") is not None:
                logger.debug(f"Skipping already resolved file: {output_file.name}")
                skipped_count += 1
                continue

            # Query blockchain for resolution using the output data
            resolved_price = get_market_resolution(data)

            if resolved_price is not None:
                # Update the file with resolution data
                if update_output_file(output_file, resolved_price):
                    updated_count += 1
                else:
                    error_count += 1
            else:
                logger.info(f"Market {data.get('query_id')} not yet resolved, skipping")
                skipped_count += 1

        except Exception as e:
            logger.error(f"Error processing {output_file.name}: {str(e)}")
            error_count += 1

    logger.info(
        f"Processing complete. Processed: {processed_count}, Updated: {updated_count}, Errors: {error_count}, Skipped: {skipped_count}"
    )


def main():
    logger.info(
        "🔍 Starting UMA Proposal Finalizer - Updating unresolved markets with blockchain data 🔄"
    )

    # Process output files
    process_outputs()

    logger.info("✅ Proposal finalizer completed")


if __name__ == "__main__":
    main()
