#!/usr/bin/env python3
"""
Common utility functions and constants used across the UMA Large Language Oracle project.

This module provides:
- Blockchain contract addresses
- ABI loading utilities
- Perplexity API query functions
- Text processing utilities
- Logging setup
- UI utilities (spinner animation)
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
