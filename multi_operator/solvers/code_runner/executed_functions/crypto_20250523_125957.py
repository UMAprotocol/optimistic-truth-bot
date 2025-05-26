import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# Constants for API endpoints
HYPERLIQUID_URL = "https://app.hyperliquid.xyz/api/v1/candles"

def fetch_candles(symbol, start_time, end_time):
    """
    Fetches candle data from Hyperliquid for a given symbol within a specified time range.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        response = requests.get(HYPERLIQUID_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return None

def convert_to_utc(date_str, time_str, timezone_str):
    """
    Converts local time to UTC timestamp.
    """
    local_tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_dt = local_tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    # Define the time range and symbol
    start_date = "2025-05-22"
    end_date = "2025-05-31"
    start_time = "12:00"
    end_time = "23:59"
    timezone_str = "US/Eastern"
    symbol = "HYPE/USDC"

    # Convert start and end times to UTC timestamps
    start_timestamp = convert_to_utc(start_date, start_time, timezone_str)
    end_timestamp = convert_to_utc(end_date, end_time, timezone_str)

    # Fetch candle data
    candles = fetch_candles(symbol, start_timestamp, end_timestamp)
    if candles is None:
        print("recommendation: p4")
        return

    # Determine if a new all-time high was reached
    high_prices = [candle['high'] for candle in candles if 'high' in candle]
    if not high_prices:
        print("recommendation: p4")
        return

    current_max_high = max(high_prices)
    historical_max_high = 100  # This should be replaced with the actual historical max high from persistent storage or previous data

    if current_max_high > historical_max_high:
        print("recommendation: p2")  # Yes, new all-time high
    else:
        print("recommendation: p1")  # No new all-time high

if __name__ == "__main__":
    main()