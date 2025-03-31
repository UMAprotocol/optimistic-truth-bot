#!/usr/bin/env python3
"""
Script to find a Polymarket market by its neg_risk_request_id from a JSON data dump.
"""

import argparse
import json
import sys
import os

# Add the parent directory to sys.path to import common.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import find_market_by_neg_risk_request_id, setup_logging


def examine_json_structure(data):
    """
    Examine the structure of the JSON data to help with debugging.

    Args:
        data: The loaded JSON data

    Returns:
        A string describing the structure
    """
    if isinstance(data, dict):
        keys = list(data.keys())
        top_level_keys = keys[:10] if len(keys) > 10 else keys
        sample_values = []
        for key in top_level_keys[:3]:  # Only examine a few values
            if isinstance(data[key], dict):
                sample_values.append(f"{key}: dict with {len(data[key])} keys")
            elif isinstance(data[key], list):
                sample_values.append(f"{key}: list with {len(data[key])} items")
            else:
                sample_values.append(f"{key}: {type(data[key]).__name__}")

        return (
            f"Dictionary with {len(keys)} keys. "
            f"Top level keys: {', '.join(top_level_keys)}. "
            f"Sample values: {'; '.join(sample_values)}"
        )

    elif isinstance(data, list):
        sample_types = []
        for i, item in enumerate(data[:3]):  # Only examine a few items
            if isinstance(item, dict):
                keys = list(item.keys())
                sample_keys = keys[:5] if len(keys) > 5 else keys
                sample_types.append(f"Item {i}: dict with keys {sample_keys}")
            elif isinstance(item, list):
                sample_types.append(f"Item {i}: list with {len(item)} items")
            else:
                sample_types.append(f"Item {i}: {type(item).__name__}")

        return f"List with {len(data)} items. Sample items: {'; '.join(sample_types)}"

    else:
        return f"Data is a {type(data).__name__}, not a dict or list"


def main():
    """Main function to parse arguments and find market by neg_risk_request_id."""
    # Set up logging
    logger = setup_logging("find_market", "find_market.log")

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Find a Polymarket market by its neg_risk_request_id from a JSON data dump."
    )
    parser.add_argument(
        "neg_risk_request_id",
        help="The neg_risk_request_id to search for (e.g., 0x92a3dd7c558d6bc1594ff1d810d3275a432335a6e8bbdaccee9d8d398247ff63)",
    )
    parser.add_argument(
        "--json-file",
        help="Path to the JSON file containing Polymarket data",
        default="polymarket_data/clob_dump.json",
    )
    parser.add_argument(
        "--output-file",
        help="Path to save the results (optional)",
    )
    parser.add_argument(
        "--examine-structure",
        action="store_true",
        help="Examine and display the JSON structure for debugging",
    )
    args = parser.parse_args()

    # Load the JSON data
    try:
        logger.info(f"Loading data from {args.json_file}")
        with open(args.json_file, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {args.json_file}")
        print(f"Error: File not found: {args.json_file}")
        return 1
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format in {args.json_file}")
        print(f"Error: Invalid JSON format in {args.json_file}")
        return 1

    # Examine JSON structure if requested
    if args.examine_structure:
        structure_info = examine_json_structure(data)
        logger.info(f"JSON structure: {structure_info}")
        print(f"JSON structure: {structure_info}")

    # Find the market by neg_risk_request_id
    logger.info(
        f"Searching for market with neg_risk_request_id: {args.neg_risk_request_id}"
    )
    market = find_market_by_neg_risk_request_id(data, args.neg_risk_request_id)

    if market:
        logger.info(f"Found market: {market.get('question', 'Unknown market')}")

        # Save to output file if specified
        if args.output_file:
            with open(args.output_file, "w") as f:
                json.dump(market, f, indent=2)
            logger.info(f"Saved market data to {args.output_file}")
            print(f"Market data saved to {args.output_file}")
        else:
            # Pretty print the market data to stdout
            print(json.dumps(market, indent=2))

        return 0
    else:
        logger.warning(
            f"No market found with neg_risk_request_id: {args.neg_risk_request_id}"
        )
        print(f"No market found with neg_risk_request_id: {args.neg_risk_request_id}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
