import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API URLs
PRIMARY_BINANCE_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_binance_data(symbol, interval, start_time, end_time, use_proxy=False):
    """
    Fetches data from Binance API or a proxy endpoint.
    """
    url = PROXY_BINANCE_API_URL if use_proxy else PRIMARY_BINANCE_API_URL
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data[0]  # Return the first (and only) candle
    except requests.RequestException as e:
        logging.error(f"Failed to fetch data from {'proxy' if use_proxy else 'primary'} endpoint: {e}")
        if not use_proxy:
            raise  # If already using primary and it fails, raise the exception
        else:
            # Fallback to primary endpoint if proxy fails
            return fetch_binance_data(symbol, interval, start_time, end_time, use_proxy=False)

def get_utc_timestamp_for_date(date_str, hour, minute, timezone_str):
    """
    Converts local time to UTC timestamp.
    """
    local_tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {hour}:{minute}", "%Y-%m-%d %H:%M")
    local_dt = local_tz.localize(local_time)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)  # Convert to milliseconds

def main():
    # Specific date and time for the event
    event_date = "2025-06-15"
    event_hour = 7  # 7 AM
    event_minute = 0
    event_timezone = "US/Eastern"
    symbol = "BTCUSDT"
    interval = "1h"

    # Convert event time to UTC timestamp
    start_time = get_utc_timestamp_for_date(event_date, event_hour, event_minute, event_timezone)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    # Fetch data from Binance using the proxy first, then fallback to primary if needed
    try:
        candle_data = fetch_binance_data(symbol, interval, start_time, end_time, use_proxy=True)
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])

        # Determine market resolution based on price change
        if close_price >= open_price:
            recommendation = "p2"  # Up
        else:
            recommendation = "p1"  # Down

        print(f"recommendation: {recommendation}")
    except Exception as e:
        logging.error(f"Error processing the market resolution: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()