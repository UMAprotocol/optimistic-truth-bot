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

def fetch_binance_data(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Close price
    except Exception as e:
        logger.error(f"Proxy failed, error: {e}, trying primary API")
        try:
            # Fallback to the primary API endpoint
            response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data[0][4])  # Close price
        except Exception as e:
            logger.error(f"Primary API failed, error: {e}")
            raise

def convert_to_utc_timestamp(date_str, hour, minute, timezone_str):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {hour}:{minute}", "%Y-%m-%d %H:%M")
    local_dt = tz.localize(local_time)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    """
    Main function to determine if the price of SOLUSDT went up or down between two specific times.
    """
    try:
        # Define the times to check
        start_date = "2025-06-04"
        end_date = "2025-06-05"
        hour = 12
        minute = 0
        timezone_str = "US/Eastern"
        symbol = "SOLUSDT"

        # Convert times to UTC timestamps
        start_time = convert_to_utc_timestamp(start_date, hour, minute, timezone_str)
        end_time = convert_to_utc_timestamp(end_date, hour, minute, timezone_str)

        # Fetch close prices
        close_price_start = fetch_binance_data(symbol, start_time, start_time + 60000)
        close_price_end = fetch_binance_data(symbol, end_time, end_time + 60000)

        # Determine the resolution
        if close_price_end > close_price_start:
            recommendation = "p2"  # Up
        elif close_price_end < close_price_start:
            recommendation = "p1"  # Down
        else:
            recommendation = "p3"  # 50-50

        print(f"recommendation: {recommendation}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()