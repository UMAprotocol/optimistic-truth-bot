#!/usr/bin/env python3
"""
Binance Price Query Tool

Usage:
    python binance_price_query.py --symbol "BTCUSDT" --timestamp "2025-06-05 05:00:00" --timezone "US/Eastern" --interval "1h"

Returns:
    The closing price for the specified interval
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler()]
)
log = logging.getLogger(__name__)


def get_binance_klines(symbol, interval, start_time_ms, end_time_ms=None):
    """Fetch klines (candlestick) data from Binance API."""
    base_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "startTime": start_time_ms,
        "limit": 1,
    }
    if end_time_ms:
        params["endTime"] = end_time_ms

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        log.error(f"Error fetching data from Binance: {e}")
        return None


def get_price_at_time(symbol, timestamp_str, timezone_str="US/Eastern", interval="1h"):
    """Get the closing price for a symbol at a specific time."""
    try:
        # Convert timestamp to UTC
        local_tz = pytz.timezone(timezone_str)
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        local_time = local_tz.localize(timestamp)
        utc_time = local_time.astimezone(pytz.UTC)

        # Convert to milliseconds timestamp
        start_ms = int(utc_time.timestamp() * 1000)

        # For hourly candles, we want the full hour
        if interval == "1h":
            end_ms = start_ms + (60 * 60 * 1000)  # Add 1 hour
        else:
            # For other intervals, add the corresponding time
            interval_minutes = {
                "1m": 1,
                "3m": 3,
                "5m": 5,
                "15m": 15,
                "30m": 30,
                "1h": 60,
                "2h": 120,
                "4h": 240,
                "6h": 360,
                "8h": 480,
                "12h": 720,
                "1d": 1440,
            }
            minutes = interval_minutes.get(interval, 60)
            end_ms = start_ms + (minutes * 60 * 1000)

        # Get the kline data
        klines = get_binance_klines(symbol, interval, start_ms, end_ms)

        if not klines:
            log.error(f"No data found for {symbol} at {timestamp_str} {timezone_str}")
            return None

        # Extract closing price from the kline data
        # Kline format: [Open time, Open, High, Low, Close, Volume, Close time, ...]
        close_price = float(klines[0][4])

        return close_price

    except Exception as e:
        log.error(f"Error getting price: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Get cryptocurrency price from Binance"
    )
    parser.add_argument("--symbol", required=True, help="Trading pair (e.g., BTCUSDT)")
    parser.add_argument(
        "--timestamp", required=True, help="Timestamp (YYYY-MM-DD HH:MM:SS)"
    )
    parser.add_argument(
        "--timezone", default="US/Eastern", help="Timezone (default: US/Eastern)"
    )
    parser.add_argument(
        "--interval",
        default="1h",
        help="Candle interval (1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    args = parser.parse_args()

    # Set logging level based on verbose flag
    log.setLevel(logging.DEBUG if args.verbose else logging.INFO)

    try:
        price = get_price_at_time(
            args.symbol, args.timestamp, args.timezone, args.interval
        )

        if price is not None:
            if args.verbose:
                log.info(
                    f"Price for {args.symbol} at {args.timestamp} {args.timezone} ({args.interval} candle): {price}"
                )
            print(f"{price}")
        else:
            log.error("Failed to get price")
            sys.exit(1)

    except Exception as e:
        log.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
