#!/usr/bin/env python3
"""
Common utility functions for UMA Multi-Operator System.
Handles API calls, response processing, and recommendation validation.
"""

import json
import re
import time
import threading
import sys
import logging
import os
import requests
from openai import OpenAI
from datetime import datetime
from pathlib import Path

# Constants for Polymarket API
POLYMARKET_PRICES_API = "https://clob.polymarket.com/prices"


def spinner(message, verbose=False, interval=0.1):
    """Display a spinner with a message if verbose mode is enabled,
    otherwise only show updates every 5 seconds.

    Returns a generator that yields on each tick.
    """
    # More visible Unicode spinner with smoother animation
    spinner_chars = "⣾⣽⣻⢿⡿⣟⣯⣷"
    # ANSI colors for better visibility
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    i = 0
    start_time = time.time()
    last_update_time = time.time()

    # Clear the spinner line (used for cleanup)
    def clear_line():
        if verbose:
            sys.stdout.write("\r" + " " * (len(message) + 40) + "\r")
            sys.stdout.flush()

    try:
        while True:
            try:
                if verbose:
                    # In verbose mode, show spinning animation with color
                    elapsed = time.time() - start_time
                    elapsed_str = f"{elapsed:.1f}s"
                    colored_spinner = (
                        f"{BLUE}{BOLD}{spinner_chars[i % len(spinner_chars)]}{RESET}"
                    )
                    sys.stdout.write(f"\r{message} {colored_spinner} [{elapsed_str}]")
                    sys.stdout.flush()
                else:
                    # In non-verbose mode, only update every 5 seconds with timestamp
                    current_time = time.time()
                    if current_time - last_update_time >= 5:
                        elapsed = current_time - start_time
                        elapsed_str = f"{elapsed:.1f}s"
                        sys.stdout.write(f"\r{message} [{elapsed_str}]")
                        sys.stdout.flush()
                        last_update_time = current_time

                i += 1

                # Sleep before yielding to reduce CPU usage
                time.sleep(interval)

                # Yield control back to caller
                yield

            except KeyboardInterrupt:
                # Clean up display on interrupt
                clear_line()
                raise

    except GeneratorExit:
        # Clean up when generator is closed
        clear_line()

    finally:
        # Final cleanup
        clear_line()


def setup_logging(module_name, log_file):
    """Set up logging configuration for a module."""
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

    # ANSI color codes for terminal output
    COLORS = {
        "RESET": "\033[0m",
        "BLACK": "\033[30m",
        "RED": "\033[31m",
        "GREEN": "\033[32m",
        "YELLOW": "\033[33m",
        "BLUE": "\033[34m",
        "MAGENTA": "\033[35m",
        "CYAN": "\033[36m",
        "WHITE": "\033[37m",
        "BOLD": "\033[1m",
        "UNDERLINE": "\033[4m",
        "BG_BLACK": "\033[40m",
        "BG_RED": "\033[41m",
        "BG_GREEN": "\033[42m",
        "BG_YELLOW": "\033[43m",
        "BG_BLUE": "\033[44m",
        "BG_MAGENTA": "\033[45m",
        "BG_CYAN": "\033[46m",
        "BG_WHITE": "\033[47m",
    }

    # Custom formatter for console output
    class ColoredFormatter(logging.Formatter):
        def format(self, record):
            # Set colors based on log level
            if record.levelno == logging.INFO:
                level_color = COLORS["BOLD"] + COLORS["GREEN"]
            elif record.levelno == logging.WARNING:
                level_color = COLORS["BOLD"] + COLORS["YELLOW"]
            elif record.levelno == logging.ERROR or record.levelno == logging.CRITICAL:
                level_color = COLORS["BOLD"] + COLORS["RED"]
            else:
                level_color = COLORS["RESET"]

            # Format timestamp
            timestamp = self.formatTime(record, "%H:%M:%S")

            # Get module name and make it consistent length
            module = record.name[:15].ljust(15)

            # Format the level name in color
            level_name = f"{level_color}{record.levelname:<8}{COLORS['RESET']}"

            # Complete format
            return f"{timestamp} ┃ {COLORS['CYAN']}{module}{COLORS['RESET']} ┃ {level_name} ┃ {record.getMessage()}"

    # Create and configure file handler (standard format for logs)
    file_handler = logging.FileHandler(log_path)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Create and configure console handler (colored, cleaner format)
    console_handler = logging.StreamHandler()
    console_formatter = ColoredFormatter()
    console_handler.setFormatter(console_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Create and return specific module logger
    logger = logging.getLogger(module_name)
    return logger


def query_perplexity(prompt, api_key, system_prompt=None, verbose=False):
    """
    Query the Perplexity API.

    Args:
        prompt (str): The user prompt content
        api_key (str): Perplexity API key
        system_prompt (str, optional): Custom system prompt to use
        verbose (bool): Whether to print verbose output

    Returns:
        API response object
    """
    # Initialize client without timeout to allow long-running queries
    client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    if verbose:
        print("Sending request to Perplexity API...")
        print("Messages being sent to API:")
        for msg in messages:
            print(f"\nRole: {msg['role']}")
            print(f"Content:\n{msg['content']}\n")
            print("-" * 80)
        print(
            "\033[33m⏳ This may take a minute or longer. Press Ctrl+C to cancel.\033[0m"
        )

    # Use threading to run the spinner animation in the background
    spinner_active = True
    spinner_thread = None

    def run_spinner():
        spin = spinner("Waiting for Perplexity API response", verbose=verbose)
        while spinner_active:
            try:
                next(spin)
            except StopIteration:
                break

    try:
        # Start spinner in background thread if verbose mode is enabled
        if verbose:
            spinner_thread = threading.Thread(target=run_spinner)
            spinner_thread.daemon = True
            spinner_thread.start()

        # Make the API call without timeout
        response = client.chat.completions.create(
            model="sonar-deep-research",
            messages=messages,
            temperature=0.0,
        )

        return response
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        if verbose:
            print("\n\033[33m⚠️ API call canceled by user\033[0m")
        raise  # Re-raise the interrupt to be handled by the caller
    except Exception as e:
        logging.error(f"Error querying Perplexity API: {e}")
        # Return a minimal response object with error information
        return {"error": str(e), "content": "API call failed"}
    finally:
        # Stop the spinner thread
        spinner_active = False
        if spinner_thread and spinner_thread.is_alive():
            spinner_thread.join(timeout=0.5)  # Wait for thread to finish


def query_chatgpt(
    prompt, api_key, system_prompt=None, model="gpt-4-turbo", verbose=False
):
    """
    Query ChatGPT API.

    Args:
        prompt (str): The user prompt content
        api_key (str): OpenAI API key
        system_prompt (str, optional): Custom system prompt to use
        model (str): Model to use for the query
        verbose (bool): Whether to print verbose output

    Returns:
        API response object
    """
    # Initialize client without timeout to allow long-running queries
    client = OpenAI(api_key=api_key)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    if verbose:
        print("Sending request to ChatGPT API...")
        print("Messages being sent to API:")
        for msg in messages:
            print(f"\nRole: {msg['role']}")
            print(f"Content:\n{msg['content']}\n")
            print("-" * 80)
        print(
            "\033[33m⏳ This may take a minute or longer. Press Ctrl+C to cancel.\033[0m"
        )

    # Use threading to run the spinner animation in the background
    spinner_active = True
    spinner_thread = None

    def run_spinner():
        spin = spinner(f"Waiting for {model} API response", verbose=verbose)
        while spinner_active:
            try:
                next(spin)
            except StopIteration:
                break

    try:
        # Start spinner in background thread if verbose mode is enabled
        if verbose:
            spinner_thread = threading.Thread(target=run_spinner)
            spinner_thread.daemon = True
            spinner_thread.start()

        # Make the API call without timeout
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.0,
        )

        return response
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        if verbose:
            print("\n\033[33m⚠️ API call canceled by user\033[0m")
        raise  # Re-raise the interrupt to be handled by the caller
    except Exception as e:
        logging.error(f"Error querying ChatGPT API: {e}")
        # Return a minimal response object with error information
        return {"error": str(e), "content": "API call failed"}
    finally:
        # Stop the spinner thread
        spinner_active = False
        if spinner_thread and spinner_thread.is_alive():
            spinner_thread.join(timeout=0.5)  # Wait for thread to finish


def extract_recommendation(response_text):
    """Extract the recommendation (p1, p2, p3, p4) from the response text."""
    # Handle various formats including markdown, bold, parenthetical remarks
    patterns = [
        # Standard format: recommendation: p1
        r"recommendation:\s*(p[1-4])",
        # Markdown with bold or emphasis: **Recommendation**: p1 (No)
        r"\*\*Recommendation\*\*:?\s*(p[1-4]).*?(?:\n|$)",
        # Markdown with emphasis: *Recommendation*: p1 (No)
        r"\*Recommendation\*:?\s*(p[1-4]).*?(?:\n|$)",
        # Capitalized: Recommendation: p1
        r"Recommendation:?\s*(p[1-4]).*?(?:\n|$)",
        # Just the p value at the end of the text
        r"(?:recommended|final)?\s*(?:value|result|answer|outcome)?:?\s*(p[1-4])(?:\s|$|\.|\)|\n)",
    ]

    for pattern in patterns:
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            return match.group(1).lower()  # Normalize to lowercase

    # If nothing found, try a more aggressive search just for p1-p4 near the end
    lines = response_text.split("\n")
    for line in lines[-5:]:  # Check last 5 lines
        p_match = re.search(r"(p[1-4])", line, re.IGNORECASE)
        if p_match:
            return p_match.group(1).lower()

    return None


def get_question_id_short_from_prompt(user_prompt):
    """
    Extract the question ID from a user prompt for logging purposes.

    Args:
        user_prompt (str): The user prompt that might contain question ID information

    Returns:
        str: Short question ID if found, otherwise "unknown"
    """
    # Try to find query ID patterns in the prompt - common formats include:
    # 1. Hex format: 0x84db9689...
    # 2. Just the ID: 84db9689...
    # 3. In a questionId_ format: questionId_84db9689

    # Try hex format first
    hex_pattern = r"0x([0-9a-f]{8})[0-9a-f]*"
    match = re.search(hex_pattern, user_prompt, re.IGNORECASE)
    if match:
        return match.group(1)

    # Try questionId_ format
    id_pattern = r"questionId_([0-9a-f]{8})[0-9a-f]*"
    match = re.search(id_pattern, user_prompt, re.IGNORECASE)
    if match:
        return match.group(1)

    # Try finding any 8+ hex digits
    generic_hex = r"[^0-9a-f]([0-9a-f]{8})[0-9a-f]*"
    match = re.search(generic_hex, user_prompt, re.IGNORECASE)
    if match:
        return match.group(1)

    return "unknown"


def format_prompt_from_json(proposal_data):
    """Format a user prompt from the proposal data JSON."""
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
    """Extract the query ID from a proposal."""
    if isinstance(proposal_data, list) and len(proposal_data) > 0:
        return proposal_data[0].get("query_id", "")
    return proposal_data.get("query_id", "")


def get_question_id_short(query_id):
    """Get the short question ID from a full query ID."""
    if not query_id:
        return "unknown"
    return query_id[2:10] if query_id.startswith("0x") else query_id[:8]


def get_output_filename(query_id):
    """Generate a standard output filename from a query ID."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = get_question_id_short(query_id)
    return f"result_{short_id}_{timestamp}.json"


def get_block_number_from_proposal(proposal_data):
    """Extract the block number from a proposal."""
    if isinstance(proposal_data, list) and len(proposal_data) > 0:
        return proposal_data[0].get("block_number", 0)
    return proposal_data.get("block_number", 0)


def should_process_proposal(proposal_data, start_block_number=0):
    """Check if a proposal should be processed based on its block number."""
    block_number = get_block_number_from_proposal(proposal_data)
    return block_number >= start_block_number


def get_token_price(token_id: str, verbose=False) -> dict:
    """
    Fetch the current price of a token from Polymarket API.

    Args:
        token_id: The token ID to fetch the price for
        verbose: Whether to show verbose output

    Returns:
        dict: A dictionary containing the price and other information about the token
    """
    # Use threading to run the spinner animation in the background
    spinner_active = True
    spinner_thread = None

    def run_spinner():
        spin = spinner(f"Fetching price for token {token_id}", verbose=verbose)
        while spinner_active:
            try:
                next(spin)
            except StopIteration:
                break

    try:
        # Start spinner in background thread if verbose mode is enabled
        if verbose:
            spinner_thread = threading.Thread(target=run_spinner)
            spinner_thread.daemon = True
            spinner_thread.start()

        # Make request without explicit timeout to let the process be interrupted by Ctrl+C
        response = requests.get(f"{POLYMARKET_PRICES_API}/{token_id}")
        response.raise_for_status()
        data = response.json()
        return data
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        logging.warning(f"Token price fetch for {token_id} canceled by user")
        if verbose:
            print(f"\n\033[33m⚠️ Token price fetch canceled by user\033[0m")
        raise  # Re-raise to be handled by the caller
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching token price for {token_id}: {e}")
        return {"error": str(e), "price": None}
    except Exception as e:
        logging.error(f"Unexpected error fetching token price for {token_id}: {e}")
        return {"error": str(e), "price": None}
    finally:
        # Stop the spinner thread
        spinner_active = False
        if spinner_thread and spinner_thread.is_alive():
            spinner_thread.join(timeout=0.5)  # Wait for thread to finish


def validate_output_json(output_json):
    """
    Validate that the output JSON contains all required fields for backward compatibility.

    Args:
        output_json: The JSON object to validate

    Returns:
        tuple: (is_valid, missing_fields)
    """
    missing_fields = []
    
    # Check format version first - different versions have different requirements
    format_version = output_json.get("format_version", 1)
    
    if format_version == 1:
        # Version 1 - Legacy format with fields at the top level
        required_fields = [
            "query_id",
            "question_id_short",
            "proposed_price",
            "resolved_price",
            "timestamp",
            "processed_file",
            "resolved_price_outcome",
            "disputed",
            "recommendation",
            "recommendation_overridden",
            "proposed_price_outcome",
            "user_prompt",  # Original name
            "condition_id",
            "tags",
            "icon",
            "end_date_iso",
            "game_start_time"
        ]
        missing_fields = [field for field in required_fields if field not in output_json]
        
        # Check if required nested structures exist
        if "proposal_metadata" not in output_json:
            missing_fields.append("proposal_metadata")
        elif "transaction_hash" not in output_json["proposal_metadata"]:
            missing_fields.append("transaction_hash (in proposal_metadata)")
            
        # Make sure recommendation is a p-value (p1, p2, p3, p4)
        if "recommendation" in output_json and not output_json["recommendation"].startswith("p"):
            missing_fields.append("valid p-value recommendation")
    
    elif format_version == 2:
        # Version 2 - Journey-focused format with organized sections
        # Core required top-level fields
        core_fields = [
            "query_id", 
            "short_id",
            "question_id_short", 
            "timestamp",
            "format_version",
            "journey"
        ]
        
        # Check core fields
        for field in core_fields:
            if field not in output_json:
                missing_fields.append(field)
        
        # Check required sections
        required_sections = ["metadata", "market_data", "result", "proposal_metadata", "overseer_data"]
        for section in required_sections:
            if section not in output_json:
                missing_fields.append(section)
                continue
                
            # Check section contents if the section exists
            if section == "metadata":
                if "processed_file" not in output_json["metadata"]:
                    missing_fields.append("processed_file (in metadata)")
                    
            elif section == "market_data":
                market_fields = ["proposed_price", "proposed_price_outcome"]
                for field in market_fields:
                    if field not in output_json["market_data"]:
                        missing_fields.append(f"{field} (in market_data)")
                    
            elif section == "result":
                if "recommendation" not in output_json["result"]:
                    missing_fields.append("recommendation (in result)")
                elif not output_json["result"]["recommendation"].startswith("p"):
                    missing_fields.append("valid p-value recommendation (in result)")
                    
            elif section == "proposal_metadata":
                # Check for important metadata fields that should be in proposal_metadata
                important_metadata_fields = [
                    "transaction_hash",
                    "block_number",
                    "request_transaction_block_time",
                    "ancillary_data",
                    "resolution_conditions",
                    "proposed_price",
                    "proposed_price_outcome",
                    "resolved_price",
                    "resolved_price_outcome",
                    "request_timestamp",
                    "expiration_timestamp",
                    "creator",
                    "proposer"
                ]
                
                for field in important_metadata_fields:
                    if field not in output_json["proposal_metadata"]:
                        # Only add the most critical fields to missing_fields to not flood the output
                        if field in ["transaction_hash", "block_number", "ancillary_data"]:
                            missing_fields.append(f"{field} (in proposal_metadata)")
                    
            elif section == "overseer_data":
                if "recommendation_journey" not in output_json["overseer_data"]:
                    missing_fields.append("recommendation_journey (in overseer_data)")
    else:
        # Unknown format version
        missing_fields.append("valid format_version (should be 1 or 2)")
    
    # Return validation result
    return (len(missing_fields) == 0, missing_fields)
