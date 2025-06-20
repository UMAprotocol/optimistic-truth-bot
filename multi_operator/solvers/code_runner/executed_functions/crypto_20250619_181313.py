import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_candle_data(symbol, interval, start_time, end_time):
    """
    Fetches candle data for a given symbol and interval from Binance API.
    Args:
        symbol (str): The symbol to fetch data for.
        interval (str): The interval of the candle data.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    Returns:
        dict: The candle data.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }
    try:
        # Try fetching from proxy first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy failed with error {e}, trying primary API.")
        # Fallback to primary API if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]

def convert_to_utc(year, month, day, hour, minute, tz_name):
    """
    Converts local time to UTC.
    Args:
        year, month, day, hour, minute (int): Local time components.
        tz_name (str): Timezone name.
    Returns:
        datetime: UTC datetime object.
    """
    local_tz = pytz.timezone(tz_name)
    local_time = local_tz.localize(datetime(year, month, day, hour, minute))
    utc_time = local_time.astimezone(pytz.utc)
    return utc_time

def main():
    # Specific event details
    year, month, day = 2025, 6, 19
    hour, minute = 13, 0  # 1 PM ET
    symbol = "SOLUSDT"
    interval = "1h"
    tz_name = "US/Eastern"

    # Convert event time to UTC
    utc_time = convert_to_utc(year, month, day, hour, minute, tz_name)
    start_time_ms = int(utc_time.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later

    # Fetch candle data
    candle_data = fetch_candle_data(symbol, interval, start_time_ms, end_time_ms)
    if candle_data:
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])
        # Determine resolution based on price comparison
        if close_price >= open_price:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 if no data

if __name__ == "__main__":
    main()