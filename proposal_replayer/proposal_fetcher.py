#!/usr/bin/env python3
"""
UMA Proposal Fetcher - Listens for ProposePrice events, fetches on-chain data, saves to JSON.
Ignores neg risk markets.

Example: python proposal_replayer/proposal_fetcher.py --start-block 68945138
"""

from web3 import Web3
from dotenv import load_dotenv
import os, time, json, argparse, sys, codecs
import requests

print(
    "⛓️ Starting UMA Proposal Fetcher - Listening for blockchain events and processing proposals 🔍 📡"
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import (
    setup_logging,
    load_abi,
    OptimisticOracleV2,
    UmaCtfAdapter,
    price_to_outcome,
    compute_condition_id,
    get_polymarket_data,
)

logger = setup_logging("proposal_fetcher", "logs/proposal_fetcher.log")
POLL_INTERVAL_SECONDS = 30
PROPOSALS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proposals")


def clean_text(text):
    try:
        text = codecs.decode(text, "unicode_escape")
        replacements = {
            "\u201c": '"',
            "\u201d": '"',
            "\u2018": "'",
            "\u2019": "'",
            "\u2013": "-",
            "\u2014": "--",
            "\u00e2\u0080\u0099": "'",
            "\u00e2\u0080\u009c": '"',
            "\u00e2\u0080\u009d": '"',
            "\\n": "\n",
            "\\r": "",
            "\\t": " ",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    except Exception:
        return text


def process_ancillary_data(data):
    if isinstance(data, str):
        data = (
            bytes.fromhex(data[2:]) if data.startswith("0x") else data.encode("utf-8")
        )

    data_hex = "0x" + data.hex()

    try:
        decoded = clean_text(data.decode("utf-8"))

        if "res_data:" in decoded:
            parts = decoded.split("res_data:", 1)
            question_part = parts[0].strip()
            res_part = parts[1]

            if "Updates made by" in res_part:
                res_part = res_part.split("Updates made by", 1)[0]

            res_part = res_part.strip()
            if res_part.endswith(","):
                res_part = res_part[:-1].strip()

            resolution = "res_data:" + res_part.strip()
        else:
            question_part = decoded
            resolution = "x"

        return data_hex, question_part, resolution
    except Exception:
        return data_hex, data_hex, "x"


def query_adapter_for_question(w3, adapter_address, question_id):
    adapter_contract = w3.eth.contract(
        address=adapter_address, abi=load_abi("UmaCtfAdapter.json")
    )

    try:
        question_data = adapter_contract.functions.questions(question_id).call()

        timestamp, reward, proposal_bond = (
            question_data[0],
            question_data[1],
            question_data[2],
        )
        resolved, creator, ancillary_data = (
            question_data[4],
            question_data[8],
            question_data[9],
        )

        if creator == "0x0000000000000000000000000000000000000000":
            logger.info(f"IGNORE: Found neg risk market for question_id {question_id}")
            return {"found": False, "neg_risk_market": True}

        _, ancillary_data_clean, resolution_conditions = process_ancillary_data(
            ancillary_data
        )

        try:
            updates = adapter_contract.functions.getUpdates(question_id, creator).call()
            string_updates = []
            for update in updates:
                try:
                    string_updates.append(update.decode("utf-8"))
                except Exception:
                    string_updates.append(
                        "0x" + update.hex()
                        if isinstance(update, bytes)
                        else str(update)
                    )
        except Exception:
            string_updates = []

        return {
            "query_id": question_id,
            "unix_timestamp": timestamp,
            "ancillary_data": ancillary_data_clean,
            "resolution_conditions": resolution_conditions,
            "updates": string_updates,
            "creator": creator,
            "proposal_bond": proposal_bond,
            "reward_amount": reward,
            "resolved": resolved,
            "found": True,
        }
    except Exception as e:
        return {"found": False, "error": str(e)}


def listen_for_propose_price_events(start_block=None):
    load_dotenv()
    w3 = Web3(Web3.HTTPProvider(os.getenv("POLYGON_RPC_URL")))
    logger.info(f"Connected to chain: {w3.is_connected()}")

    oov2_contract = w3.eth.contract(
        address=OptimisticOracleV2, abi=load_abi("OptimisticOracleV2.json")
    )
    current_block = w3.eth.block_number
    latest_block = start_block if start_block is not None else current_block

    logger.info(f"Starting from block {latest_block} (current: {current_block})")
    os.makedirs(PROPOSALS_DIR, exist_ok=True)

    try:
        while True:
            current_block = w3.eth.block_number

            if current_block <= latest_block:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            logger.info(f"Checking blocks {latest_block} to {current_block}...")
            events = oov2_contract.events.ProposePrice.get_logs(
                from_block=latest_block, to_block=current_block
            )

            if not events:
                logger.info(
                    f"Found no new events. Checking again in {POLL_INTERVAL_SECONDS} seconds."
                )
                latest_block = current_block + 1
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            for event in events:
                logger.info(
                    f"ProposePrice Event: {event.transactionHash.hex()} - Block: {event.blockNumber}"
                )

                ancillary_data = event["args"].get("ancillaryData", b"")
                data_hex, data_clean, resolution = process_ancillary_data(
                    ancillary_data
                )

                question_id = (
                    "0x"
                    + w3.keccak(
                        ancillary_data
                        if isinstance(ancillary_data, bytes)
                        else (
                            ancillary_data.encode("utf-8")
                            if isinstance(ancillary_data, str)
                            else b""
                        )
                    ).hex()
                )
                logger.info(f"QuestionID: {question_id}")

                adapter_result = query_adapter_for_question(
                    w3, UmaCtfAdapter, question_id
                )

                if adapter_result.get(
                    "neg_risk_market", False
                ) or not adapter_result.get("found", False):
                    logger.info(f"Skipping market for {question_id}")
                    continue

                result = {
                    "query_id": question_id,
                    "transaction_hash": "0x" + event.transactionHash.hex(),
                    "block_number": event.blockNumber,
                    "ancillary_data": data_clean,
                    "ancillary_data_hex": data_hex,
                    "resolution_conditions": resolution,
                    "proposed_price": event["args"].get("proposedPrice", 0),
                    "proposed_price_outcome": price_to_outcome(
                        event["args"].get("proposedPrice", 0)
                    ),
                    "resolved_price": None,
                    "resolved_price_outcome": None,
                    "unix_timestamp": event["args"].get("timestamp", 0),
                    "creator": event["args"].get("requester", ""),
                    "proposal_bond": 0,
                    "reward_amount": 0,
                    "updates": [],
                }

                for key in [
                    "unix_timestamp",
                    "creator",
                    "proposal_bond",
                    "reward_amount",
                    "updates",
                ]:
                    if key in adapter_result and adapter_result[key]:
                        result[key] = adapter_result[key]

                logger.debug(f"Creator: {result['creator']}")
                logger.debug(f"Unix timestamp: {result['unix_timestamp']}")
                logger.debug(f"Proposal bond: {result['proposal_bond']}")

                save_proposal(result, question_id)

            latest_block = current_block + 1
            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logger.info("Event listener stopped by user.")
    except Exception as e:
        logger.error(f"Error in event listener: {e}")


def enrich_proposal_with_polymarket_data(result, question_id):
    """Enrich proposal with data from Polymarket API."""
    try:
        # Compute condition ID
        condition_id = compute_condition_id(UmaCtfAdapter, question_id, 2)
        logger.info(f"Querying Polymarket API for condition_id: {condition_id}")

        # Fetch market data
        poly_data = get_polymarket_data(condition_id)
        if not poly_data:
            logger.warning(f"No Polymarket data found for {question_id}")
            return result

        # Extract required fields
        result["tags"] = poly_data.get("tags", [])
        result["icon"] = poly_data.get("icon", "")
        result["end_date_iso"] = poly_data.get("end_date_iso", "")
        result["game_start_time"] = poly_data.get("game_start_time", "")

        logger.info(f"Added Polymarket data for {question_id}: tags={result['tags']}")
        return result

    except Exception as e:
        logger.error(f"Error enriching proposal with Polymarket data: {e}")
        return result


def save_proposal(result, question_id):
    question_id_short = question_id[2:10]  # First 8 chars after 0x
    result_filename = os.path.join(
        PROPOSALS_DIR, f"questionId_{question_id_short}.json"
    )

    # Enrich with Polymarket data
    result = enrich_proposal_with_polymarket_data(result, question_id)

    proposals = [result]

    if os.path.exists(result_filename):
        try:
            with open(result_filename, "r") as f:
                existing_data = json.load(f)

            if not isinstance(existing_data, list):
                existing_data = [existing_data]

            is_duplicate = any(
                proposal.get("query_id") == result["query_id"]
                and proposal.get("proposed_price") == result["proposed_price"]
                for proposal in existing_data
            )

            if not is_duplicate:
                proposals = existing_data + [result]
                logger.info(f"Appended new proposal to {result_filename}")
            else:
                logger.info(f"Skipped duplicate proposal for {question_id}")
                return
        except Exception as e:
            logger.error(f"Error reading existing file: {e}")

    with open(result_filename, "w") as f:
        json.dump(proposals, f, indent=2)
    logger.info(f"Saved proposal to {result_filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Listen for ProposePrice events on OptimisticOracleV2"
    )
    parser.add_argument(
        "--start-block",
        type=int,
        help="Block number to start listening from (default: latest)",
    )
    args = parser.parse_args()

    logger.info("Starting ProposePrice event subscriber...")
    listen_for_propose_price_events(args.start_block)
