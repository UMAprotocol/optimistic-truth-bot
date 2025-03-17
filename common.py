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
from openai import OpenAI
from prompt import create_messages
import logging
import os

MARKET_CATEGORIES = [
    "Breaking News",
    "Trump Presidency",
    "Economy",
    "Ukraine",
    "March Madness",
    "Trade War",
    "AI",
    "Geopolitics",
    "NFL",
    "DOGE",
    "Crypto Prices",
    "Epstein",
    "Gaza",
    "South Korea",
    "Declassification",
    "Kanye",
    "TikTok",
    "Recurring",
    "Cabinet",
    "Bitcoin",
    "German Election",
    "Israel",
    "Trump 100 Days",
    "OpenAI",
    "Weather",
    "Elon Musk",
    "Middle East",
    "Fed Rates",
    "Global Elections",
    "Canada",
    "Movies",
]

OptimisticOracleV2 = "0xeE3Afe347D5C74317041E2618C49534dAf887c24"
NegRiskUmaCtfAdapter = "0x2F5e3684cb1F318ec51b00Edba38d79Ac2c0aA9d"
UmaCtfAdapter = "0x6A9D222616C90FcA5754cd1333cFD9b7fb6a4F74"
yesOrNoIdentifier = "0x5945535f4f525f4e4f5f51554552590000000000000000000000000000000000"


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
