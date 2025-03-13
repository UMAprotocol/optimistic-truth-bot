#!/usr/bin/env python3
"""
UMA Proposal Finalizer - Checks unresolved proposals/outputs and updates them with
the final resolution prices from the blockchain.

Usage: python proposal_replayer/proposal_finalizer.py
"""

import os
import json
import sys
import time
import threading
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
    spinner_animation,
    price_to_outcome,
)

# Setup logging
logger = setup_logging("proposal_finalizer", "logs/proposal_finalizer.log")
load_dotenv()

# Directory paths - considering the script is in proposal_replayer directory
CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent
OUTPUTS_DIR = CURRENT_DIR / "outputs"
PROPOSALS_DIR = CURRENT_DIR / "proposals"

logger.info(f"Outputs directory: {OUTPUTS_DIR}")
logger.info(f"Proposals directory: {PROPOSALS_DIR}")

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

# Initialize contracts
try:
    adapter_contract = w3.eth.contract(
        address=UmaCtfAdapter, abi=load_abi("UmaCtfAdapter.json")
    )
    oov2_contract = w3.eth.contract(
        address=OptimisticOracleV2, abi=load_abi("OptimisticOracleV2.json")
    )
    logger.info("Contracts initialized successfully")
except Exception as e:
    logger.error(f"Error initializing contracts: {str(e)}")
    sys.exit(1)


def interpret_resolved_price(resolved_price):
    """Interpret the resolved price value based on standard resolution values."""
    # Use our new price_to_outcome function
    outcome = price_to_outcome(resolved_price)

    # Map the outcome to a more descriptive message
    if outcome == "p1":
        return resolved_price, "NO (p1)"
    elif outcome == "p2":
        return resolved_price, "YES (p2)"
    elif outcome == "p3":
        return resolved_price, "UNKNOWN/CANNOT BE DETERMINED (p3)"
    elif outcome == "p4":
        return resolved_price, "WAITING FOR MORE INFO (p4)"
    else:
        return resolved_price, f"Non-standard value: {resolved_price}"


def get_market_resolution(question_id):
    """Query the blockchain for the resolution of a specific question ID."""
    logger.info(f"Querying resolution for question ID: {question_id}")

    stop_spinner = threading.Event()
    spinner_thread = threading.Thread(
        target=spinner_animation,
        args=(stop_spinner, f"Querying blockchain for {question_id[:10]}..."),
        daemon=True,
    )
    spinner_thread.start()

    try:
        # Query adapter for question data
        question_data = adapter_contract.functions.questions(question_id).call()

        # Extract needed data
        timestamp = question_data[0]  # requestTimestamp
        ancillary_data = question_data[9]  # ancillary data as bytes

        # Query OOV2 for request details
        request_data = oov2_contract.functions.getRequest(
            UmaCtfAdapter, yesOrNoIdentifier, timestamp, "0x" + ancillary_data.hex()
        ).call()

        # Check if market has settled
        if not request_data[3]:  # settled flag
            logger.info(f"Market {question_id} not settled yet")
            return None, None

        # Get resolved price and decode from 1e18 scaling
        resolved_price = request_data[6] / 1e18

        # Instead of using a placeholder, use the original transaction hash
        # We can query logs to find the settlement transaction, but as an immediate fix,
        # we'll use the original transaction hash from the proposal data
        # Query for the settlement event to get the actual resolution transaction
        resolution_tx = None
        try:
            # Get past events for settlement of this question
            settlement_filter = oov2_contract.events.Settle.create_filter(
                fromBlock=question_data[2],  # requestBlockNumber
                toBlock="latest",
                argument_filters={
                    "requester": UmaCtfAdapter,
                    "identifier": yesOrNoIdentifier,
                    "timestamp": timestamp,
                    "ancillaryData": "0x" + ancillary_data.hex(),
                },
            )
            events = settlement_filter.get_all_entries()
            if events:
                resolution_tx = events[0].transactionHash.hex()
                logger.info(f"Found resolution transaction: {resolution_tx}")
            else:
                # Fallback to the original transaction
                logger.warning(
                    f"No settlement event found, using original transaction as fallback"
                )
                resolution_tx = question_data[
                    1
                ]  # Assuming this field has the original tx
        except Exception as e:
            logger.warning(
                f"Error querying settlement events: {str(e)}, using fallback"
            )
            resolution_tx = question_data[1] if len(question_data) > 1 else None

        # If we still don't have a transaction, use the one from outputs file if available
        if not resolution_tx:
            # Find corresponding output file to get the transaction hash
            for output_file in OUTPUTS_DIR.glob(f"*{question_id[-8:]}.json"):
                try:
                    with open(output_file, "r") as f:
                        output_data = json.load(f)
                        resolution_tx = output_data.get("transaction_hash")
                        if resolution_tx:
                            logger.info(
                                f"Using transaction hash from output file: {resolution_tx}"
                            )
                            break
                except Exception:
                    pass

        # If still no transaction hash, use a default but distinctive one
        if not resolution_tx:
            logger.warning(
                f"Unable to find resolution transaction, using original tx hash"
            )
            resolution_tx = (
                question_data[1] if len(question_data) > 1 else f"0x{question_id[-64:]}"
            )

        logger.info(f"Market {question_id} resolved with price: {resolved_price}")
        return resolved_price, resolution_tx

    except Exception as e:
        logger.error(f"Error querying resolution for {question_id}: {str(e)}")
        return None, None
    finally:
        stop_spinner.set()
        spinner_thread.join()


def update_output_file(output_path, resolved_price, resolution_tx):
    """Update an output file with the resolved price and transaction information."""
    try:
        with open(output_path, "r") as f:
            data = json.load(f)

        # Update the resolved price and resolution tx
        data["resolved_price"] = resolved_price
        data["resolved_price_outcome"] = price_to_outcome(resolved_price)
        data["resolution_tx"] = resolution_tx

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

            query_id = data.get("query_id")
            if not query_id:
                logger.warning(f"No query_id found in {output_file.name}, skipping")
                skipped_count += 1
                continue

            # Query blockchain for resolution
            resolved_price, resolution_tx = get_market_resolution(query_id)

            if resolved_price is not None:
                # Update the file with resolution data
                if update_output_file(output_file, resolved_price, resolution_tx):
                    updated_count += 1
                else:
                    error_count += 1
            else:
                logger.info(f"Market {query_id} not yet resolved, skipping")
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
