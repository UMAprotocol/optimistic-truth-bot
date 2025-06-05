#!/usr/bin/env python3
"""
Binance Price Up/Down Resolver

Determines if a trading pair's price on Binance went up or down over a specific time period.
Uses binance_price_query.py to fetch the actual price data.

Usage:
    python binance_price_up_down.py --pair "BTCUSDT" --timestamp "2025-06-05 05:00:00" --timezone "US/Eastern"

Returns:
    "Winner: Up" if price increased or stayed the same
    "Winner: Down" if price decreased
    "Status: PENDING" if price data is not available
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
import subprocess
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler()]
)
log = logging.getLogger(__name__)


def get_price(pair, timestamp_str, timezone="US/Eastern", interval="1h"):
    """Get price using the binance_price_query script."""
    try:
        cmd = [
            "python",
            "binance_price_query.py",
            "--symbol",
            pair,
            "--timestamp",
            timestamp_str,
            "--timezone",
            timezone,
            "--interval",
            interval,
        ]

        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Run the command and capture output
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=script_dir)

        if result.returncode != 0:
            log.error(f"Error getting price: {result.stderr}")
            return None

        return float(result.stdout.strip())

    except Exception as e:
        log.error(f"Error running price query: {e}")
        return None


def determine_price_change(pair, timestamp_str, timezone="US/Eastern"):
    """Determine if price went up or down over the 1-hour period."""
    try:
        # Get timestamp for the start of the candle
        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

        # Get the opening and closing prices for the 1-hour candle
        open_price = get_price(pair, timestamp_str, timezone, "1h")

        if open_price is None:
            log.error("Could not get opening price")
            return "Status: PENDING", f"Could not get opening price for {pair}"

        # Get the closing price (1 hour later)
        close_dt = dt + timedelta(hours=1)
        close_timestamp = close_dt.strftime("%Y-%m-%d %H:%M:%S")
        close_price = get_price(pair, close_timestamp, timezone, "1h")

        if close_price is None:
            log.error("Could not get closing price")
            return "Status: PENDING", f"Could not get closing price for {pair}"

        # Calculate percentage change
        percent_change = ((close_price - open_price) / open_price) * 100

        # Format the pair name for display (e.g., "BTC/USDT" from "BTCUSDT")
        display_pair = f"{pair[:-4]}/{pair[-4:]}" if pair.endswith("USDT") else pair

        # Determine result
        if percent_change >= 0:
            return (
                "Winner: Up",
                f"{display_pair} price increased by {percent_change:.2f}% ({open_price:.2f} → {close_price:.2f})",
            )
        else:
            return (
                "Winner: Down",
                f"{display_pair} price decreased by {percent_change:.2f}% ({open_price:.2f} → {close_price:.2f})",
            )

    except Exception as e:
        log.error(f"Error determining price change: {e}")
        return "Status: PENDING", f"Error: {e}"


def main():
    parser = argparse.ArgumentParser(
        description="Determine if a Binance trading pair's price went up or down"
    )
    parser.add_argument(
        "--pair", required=True, help="Trading pair (e.g., BTCUSDT, ETHUSDT)"
    )
    parser.add_argument(
        "--timestamp", required=True, help="Start timestamp (YYYY-MM-DD HH:MM:SS)"
    )
    parser.add_argument(
        "--timezone", default="US/Eastern", help="Timezone (default: US/Eastern)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    args = parser.parse_args()

    # Set logging level based on verbose flag
    log.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    try:
        result, details = determine_price_change(
            args.pair, args.timestamp, args.timezone
        )

        if args.verbose:
            log.info(details)
        print(result)

    except Exception as e:
        log.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
