#!/usr/bin/env python3
"""
Script to fetch all available markets data from Polymarket CLOB API.
Uses pagination to iterate through all results and saves them to a JSON file.
Can run in polling mode to periodically update the data.
"""

import json
import time
import requests
import logging
from datetime import datetime
import os
import argparse

# Import from parent directory
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import POLYMARKET_API_BASE, setup_logging

# Setup logging
logger = setup_logging("fetch_all_clob_markets", "fetch_all_clob_markets.log")


def fetch_markets_page(next_cursor=None):
    """
    Fetches a single page of market data from the Polymarket API.

    Args:
        next_cursor: Pagination cursor for the next page

    Returns:
        Tuple of (markets_data, next_cursor)
    """
    url = POLYMARKET_API_BASE.rstrip("/")

    if next_cursor:
        url += f"?next_cursor={next_cursor}"

    try:
        logger.info(f"Fetching data from {url}")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        markets = data.get("data", [])
        next_cursor = data.get("next_cursor")

        logger.info(f"Fetched {len(markets)} markets, next cursor: {next_cursor}")
        return markets, next_cursor

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data: {str(e)}")
        return [], None

    finally:
        # Rate limiting
        time.sleep(1)


def fetch_all_markets():
    """
    Fetches all markets data by iterating through pagination.

    Returns:
        List of all market data
    """
    all_markets = []
    next_cursor = None
    page_count = 0

    while True:
        page_count += 1
        markets, next_cursor = fetch_markets_page(next_cursor)

        if not markets:
            logger.warning(f"No markets returned on page {page_count}, stopping")
            break

        all_markets.extend(markets)
        logger.info(f"Total markets collected: {len(all_markets)}")

        if not next_cursor:
            logger.info("No more pages available, finished fetching data")
            break

    return all_markets


def save_to_json(data, filename="polymarket_data.json"):
    """
    Saves the collected data to a JSON file.

    Args:
        data: Data to save
        filename: Filename, defaults to fixed name for polling mode
    """
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    filepath = os.path.join("output", filename)

    # Add a timestamp to the data structure
    output_data = {
        "markets": data,
        "count": len(data),
        "last_updated": datetime.now().isoformat(),
    }

    with open(filepath, "w") as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Data saved to {filepath}")
    return filepath


def poll_markets(interval_minutes, output_file="polymarket_data.json"):
    """
    Continuously polls the Polymarket API at the specified interval.

    Args:
        interval_minutes: Time in minutes between polls
        output_file: Name of the output file to update
    """
    interval_seconds = interval_minutes * 60

    logger.info(f"Starting polling mode - interval {interval_minutes} minutes")

    while True:
        try:
            start_time = time.time()
            logger.info(f"Poll cycle started at {datetime.now().isoformat()}")

            all_markets = fetch_all_markets()
            if all_markets:
                filepath = save_to_json(all_markets, output_file)
                logger.info(
                    f"Successfully updated {len(all_markets)} markets to {filepath}"
                )
            else:
                logger.error("No market data was collected in this poll cycle")

            # Calculate time to sleep
            elapsed = time.time() - start_time
            sleep_time = max(0, interval_seconds - elapsed)

            logger.info(
                f"Poll cycle completed in {elapsed:.2f} seconds. Next poll in {sleep_time/60:.2f} minutes"
            )
            time.sleep(sleep_time)

        except Exception as e:
            logger.exception(f"Error during poll cycle: {str(e)}")
            # Still wait before retrying on error
            logger.info(f"Retrying in {interval_seconds} seconds")
            time.sleep(interval_seconds)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch all Polymarket CLOB markets data"
    )
    parser.add_argument("--poll", action="store_true", help="Run in polling mode")
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Polling interval in minutes (default: 60)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="polymarket_data.json",
        help="Output filename (default: polymarket_data.json)",
    )
    return parser.parse_args()


def main():
    """Main function to run the script."""
    args = parse_arguments()

    if args.poll:
        logger.info(f"Starting Polymarket data fetch in polling mode")
        poll_markets(args.interval, args.output)
    else:
        logger.info("Starting one-time Polymarket data fetch")
        try:
            all_markets = fetch_all_markets()

            if all_markets:
                # Use timestamped filename for one-time runs
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = (
                    f"polymarket_data_{timestamp}.json"
                    if args.output == "polymarket_data.json"
                    else args.output
                )
                filepath = save_to_json(all_markets, filename)
                logger.info(
                    f"Successfully fetched and saved {len(all_markets)} markets to {filepath}"
                )
            else:
                logger.error("No market data was collected")

        except Exception as e:
            logger.exception(f"Unexpected error during execution: {str(e)}")


if __name__ == "__main__":
    main()
