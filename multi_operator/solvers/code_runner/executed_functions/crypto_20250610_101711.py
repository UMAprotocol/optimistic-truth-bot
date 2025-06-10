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

def get_binance_data(symbol, interval, start_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    primary_url = "https://api.binance.com/api/v3/klines"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
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
        logger.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}. Trying primary endpoint.")
        # Fallback to primary endpoint
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}")
            raise

def parse_binance_data(data):
    """
    Parses the Binance data to extract the relevant price change information.
    """
    if not data or len(data) == 0:
        logger.error("No data available to parse.")
        return None
    # Extract the opening and closing prices from the first (and only) entry
    open_price = float(data[0][1])
    close_price = float(data[0][4])
    return (close_price - open_price) / open_price * 100

def main():
    """
    Main function to determine if the Bitcoin price went up or down.
    """
    symbol = "BTCUSDT"
    interval = "1h"
    # June 9, 2025, 10 PM ET in milliseconds since epoch
    target_time = int(datetime(2025, 6, 9, 22, 0, tzinfo=pytz.timezone("US/Eastern")).timestamp() * 1000)

    try:
        data = get_binance_data(symbol, interval, target_time)
        price_change_percentage = parse_binance_data(data)
        if price_change_percentage is None:
            print("recommendation: p3")  # Unknown or no data
        elif price_change_percentage >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown or error

if __name__ == "__main__":
    main()