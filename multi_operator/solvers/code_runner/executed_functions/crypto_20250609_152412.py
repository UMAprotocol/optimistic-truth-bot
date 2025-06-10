import requests
import logging
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def get_data(symbol, interval, start_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logger.error(f"Proxy failed, error: {e}. Trying primary endpoint.")
        # Fallback to primary endpoint
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Both proxy and primary endpoints failed, error: {e}.")
            raise

def convert_to_utc(year, month, day, hour, minute, tz_str):
    """
    Converts local time to UTC timestamp.
    """
    local_tz = pytz.timezone(tz_str)
    local_time = local_tz.localize(datetime(year, month, day, hour, minute, 0))
    utc_time = local_time.astimezone(pytz.utc)
    return int(utc_time.timestamp() * 1000)

def analyze_candle(data):
    """
    Analyzes the candle data to determine if the price went up or down.
    """
    if not data or not data[0]:
        return "p3"  # Unknown or no data
    open_price = float(data[0][1])
    close_price = float(data[0][4])
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to fetch and analyze Binance candle data.
    """
    # Specific date and time for the candle
    year, month, day = 2025, 5, 30
    hour, minute = 2, 0  # 2 AM ET
    symbol = "BTCUSDT"
    interval = "1h"
    tz_str = "America/New_York"

    try:
        utc_start_time = convert_to_utc(year, month, day, hour, minute, tz_str)
        data = get_data(symbol, interval, utc_start_time)
        result = analyze_candle(data)
        print(f"recommendation: {result}")
    except Exception as e:
        logger.error(f"Failed to process data: {e}")
        print("recommendation: p3")  # Default to unknown if there's an error

if __name__ == "__main__":
    main()