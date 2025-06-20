import requests
import logging
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def fetch_eth_high_price(start_time, end_time):
    """
    Fetches the highest price of Ethereum (ETHUSDT) from Binance within a given time range.

    Args:
        start_time (int): Start time in milliseconds since the epoch.
        end_time (int): End time in milliseconds since the epoch.

    Returns:
        float: The highest price of Ethereum in the given time range.
    """
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "ETHUSDT",
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000  # Maximum limit
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        high_prices = [float(candle[2]) for candle in data]  # High price is at index 2
        return max(high_prices) if high_prices else None
    except requests.RequestException as e:
        logger.error(f"Failed to fetch data from Binance: {e}")
        return None

def check_eth_price_threshold():
    """
    Checks if the Ethereum price reached $2800 at any point in June 2025.

    Returns:
        str: 'p1' if the price did not reach $2800, 'p2' if it did, 'p3' if unknown.
    """
    # Define the time range for June 2025 in Eastern Time
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 6, 1, 0, 0, 0)).astimezone(pytz.utc)
    end_date = tz.localize(datetime(2025, 6, 30, 23, 59, 59)).astimezone(pytz.utc)

    # Convert to milliseconds since the epoch
    start_time_ms = int(start_date.timestamp() * 1000)
    end_time_ms = int(end_date.timestamp() * 1000)

    # Fetch the highest price in the range
    high_price = fetch_eth_high_price(start_time_ms, end_time_ms)

    # Determine the resolution based on the high price
    if high_price is None:
        return "p3"  # Unknown if no data could be fetched
    elif high_price >= 2800:
        return "p2"  # Yes, price reached $2800
    else:
        return "p1"  # No, price did not reach $2800

def main():
    resolution = check_eth_price_threshold()
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()