#!/usr/bin/env python3
"""
Common utility functions and constants used across the UMA Large Language Oracle project.
"""

import json
import re
import itertools
import threading
import sys
import time
import requests
from openai import OpenAI
from multi_operator.prompts.perplexity_prompt import create_messages
import logging
import os
from web3 import Web3

OptimisticOracleV2 = "0xeE3Afe347D5C74317041E2618C49534dAf887c24"
NegRiskUmaCtfAdapter = "0x2F5e3684cb1F318ec51b00Edba38d79Ac2c0aA9d"
UmaCtfAdapter = "0x6A9D222616C90FcA5754cd1333cFD9b7fb6a4F74"
yesOrNoIdentifier = "0x5945535f4f525f4e4f5f51554552590000000000000000000000000000000000"
POLYMARKET_API_BASE = "https://clob.polymarket.com/markets/"
POLYMARKET_PRICES_API = "https://clob.polymarket.com/prices"


def compute_condition_id(
    oracle_address: str, question_id: str, outcome_slot_count: int
) -> str:
    """
    Compute the condition ID used in Polymarket API queries.

    Args:
        oracle_address: The address of the oracle contract
        question_id: The query ID/question ID
        outcome_slot_count: Number of outcome slots (typically 2 for Yes/No markets)

    Returns:
        Condition ID string with 0x prefix
    """
    oracle_address = Web3.to_checksum_address(oracle_address)
    # Pack the parameters as in Solidity
    packed = Web3.solidity_keccak(
        ["address", "bytes32", "uint256"],
        [oracle_address, question_id, outcome_slot_count],
    )

    return "0x" + packed.hex()


def get_polymarket_data(condition_id: str) -> dict:
    """
    Fetch market data from Polymarket API with rate limiting.

    Args:
        condition_id: The condition ID to query

    Returns:
        JSON response from Polymarket API or None if failed
    """
    url = f"{POLYMARKET_API_BASE}{condition_id}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching Polymarket data for {condition_id}: {str(e)}")
        return None
    finally:
        time.sleep(0.5)  # 500ms between API requests


def get_token_price(token_id: str) -> dict:
    """
    Fetch token price from Polymarket Prices API.

    Args:
        token_id: The token ID to query

    Returns:
        Dictionary with token price information or None if failed
    """
    try:
        payload = [{"token_id": token_id}]
        response = requests.post(POLYMARKET_PRICES_API, json=payload)
        response.raise_for_status()
        result = response.json()
        if result and isinstance(result, list) and len(result) > 0:
            return result[0]
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching Polymarket price for token {token_id}: {str(e)}")
        return None
    finally:
        time.sleep(0.5)  # 500ms between API requests


def find_market_by_neg_risk_request_id(data, neg_risk_request_id: str) -> dict:
    """
    Find a market in Polymarket data by its neg_risk_request_id.

    Args:
        data: Polymarket data (could be a list of markets or a dictionary with nested markets)
        neg_risk_request_id: The neg_risk_request_id to search for

    Returns:
        The complete market data object or None if not found
    """
    # If data is a dictionary, try to find markets key
    if isinstance(data, dict):
        # Check if this dictionary itself has the neg_risk_request_id
        if data.get("neg_risk_request_id") == neg_risk_request_id:
            return data

        # Look for markets in common locations
        for key in ["markets", "data", "results"]:
            if key in data and isinstance(data[key], list):
                result = find_market_by_neg_risk_request_id(
                    data[key], neg_risk_request_id
                )
                if result:
                    return result

        # Recursively search all dictionary values
        for value in data.values():
            if isinstance(value, (dict, list)):
                result = find_market_by_neg_risk_request_id(value, neg_risk_request_id)
                if result:
                    return result

    # If data is a list, search each item
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                if item.get("neg_risk_request_id") == neg_risk_request_id:
                    return item

                # Recursively search nested structures
                if any(isinstance(v, (dict, list)) for v in item.values()):
                    result = find_market_by_neg_risk_request_id(
                        item, neg_risk_request_id
                    )
                    if result:
                        return result
            elif isinstance(item, (dict, list)):
                result = find_market_by_neg_risk_request_id(item, neg_risk_request_id)
                if result:
                    return result

    return None


def load_abi(filename):
    with open(f"./abi/{filename}") as f:
        return json.load(f)


def spinner_animation(stop_event, message="Processing"):
    """Display a spinner animation in the console while a process is running."""
    spinner = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
    while not stop_event.is_set():
        sys.stdout.write(f"\r{message} {next(spinner)} ")
        sys.stdout.flush()
        time.sleep(0.1)
    # Clear the spinner line when done
    sys.stdout.write("\r" + " " * (len(message) + 10) + "\r")
    sys.stdout.flush()


def query_perplexity(
    prompt, api_key, base_url="https://api.perplexity.ai", verbose=False
):
    """Query the Perplexity API."""
    client = OpenAI(api_key=api_key, base_url=base_url)
    messages = create_messages(prompt)

    if verbose:
        print("Sending request to Perplexity API...")
        print("Messages being sent to API:")
        for msg in messages:
            print(f"\nRole: {msg['role']}")
            print(f"Content:\n{msg['content']}\n")
            print("-" * 80)

    response = client.chat.completions.create(
        model="sonar-deep-research",
        messages=messages,
        temperature=0.0,
    )
    return response


def extract_recommendation(response_text):
    """Extract the recommendation (p1, p2, p3, p4) from the response text."""
    match = re.search(r"recommendation:\s*(p[1-4])", response_text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def price_to_outcome(price):
    """
    Convert a numerical price to its string representation (p1, p2, p3, p4).

    Args:
        price: Numerical price value (can be int, float, str, or scientific notation)

    Returns:
        String representing the outcome category (p1, p2, p3, or p4)
    """
    # Convert string to float if needed
    if isinstance(price, str):
        try:
            price = float(price)
        except ValueError:
            return f"Invalid price: {price}"

    # Check if price is None
    if price is None:
        return "Unresolved"

    # Normalized values (accounting for 1e18 scaling)
    if price == 0:
        return "p1"  # NO
    elif price == 1 or price == int(1e18) or price == 1e18:
        return "p2"  # YES
    elif price == 0.5 or price == int(5e17) or price == 5e17:
        return "p3"  # UNKNOWN/CANNOT BE DETERMINED
    elif (
        price
        == -57896044618658097711785492504343953926634992332820282019728.792003956564819968
        or price
        == -57896044618658097711785492504343953926634992332820282019728792003956564819968
    ):
        return "p4"  # WAITING FOR MORE INFO
    else:
        return f"Non-standard: {price}"


def setup_logging(module_name, log_file):
    """
    Set up logging configuration for a module

    Args:
        module_name: Name of the module (used in log entries)
        log_file: Path to the log file

    Returns:
        Logger instance configured for the module
    """
    # Ensure the log file has a directory component
    log_path = (
        os.path.join("logs", log_file)
        if "/" not in log_file and "\\" not in log_file
        else log_file
    )

    # Ensure logs directory exists
    os.makedirs(
        os.path.dirname(log_path) if os.path.dirname(log_path) else "logs",
        exist_ok=True,
    )

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler()],
        force=True,  # Ensure settings apply even if logging was configured elsewhere
    )

    # Create and return logger
    return logging.getLogger(module_name)
