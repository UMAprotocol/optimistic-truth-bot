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

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        logger.error(f"Proxy failed with error: {e}, trying primary endpoint.")
        # Fallback to the primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price
        except Exception as e:
            logger.error(f"Primary endpoint also failed with error: {e}")
            raise

def convert_to_utc_timestamp(date_str, hour, minute, tz_str):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(tz_str)
    local_dt = tz.localize(datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S"))
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    """
    Main function to determine if Bitcoin price went up or down between two specific times.
    """
    try:
        # Define the times to check
        start_date = "2025-06-10"
        end_date = "2025-06-11"
        hour = 12
        minute = 0
        tz_str = "US/Eastern"
        symbol = "BTCUSDT"

        # Convert times to UTC timestamps
        start_time = convert_to_utc_timestamp(start_date, hour, minute, tz_str)
        end_time = convert_to_utc_timestamp(end_date, hour, minute, tz_str)

        # Fetch close prices
        close_price_start = fetch_binance_data(symbol, "1m", start_time, start_time + 60000)
        close_price_end = fetch_binance_data(symbol, "1m", end_time, end_time + 60000)

        # Determine the resolution
        if close_price_end > close_price_start:
            recommendation = "recommendation: p2"  # Up
        elif close_price_end < close_price_start:
            recommendation = "recommendation: p1"  # Down
        else:
            recommendation = "recommendation: p3"  # 50-50

        print(recommendation)
    except Exception as e:
        logger.error(f"Failed to process due to: {e}")
        print("recommendation: p4")  # Unknown or error

if __name__ == "__main__":
    main()