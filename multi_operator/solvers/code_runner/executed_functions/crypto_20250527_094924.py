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

def fetch_hashprice_data(start_time, end_time):
    """
    Fetches the Bitcoin Hashprice data from the Hashrate Index API within the specified timeframe.

    Args:
        start_time: Start time in milliseconds since epoch
        end_time: End time in milliseconds since epoch

    Returns:
        List of hashprice data points
    """
    url = "https://data.hashrateindex.com/network-data/bitcoin-hashprice-index"
    params = {
        "start": start_time,
        "end": end_time,
        "currency": "USD",
        "hashrate_units": "PH/s",
        "interval": "3M"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        logger.error(f"Failed to fetch hashprice data: {e}")
        return None

def check_price_threshold(data, threshold=57.50001):
    """
    Checks if any data point in the provided hashprice data exceeds the threshold.

    Args:
        data: List of hashprice data points
        threshold: Price threshold to check against

    Returns:
        True if any data point exceeds the threshold, False otherwise
    """
    for point in data:
        if point['price'] >= threshold:
            return True
    return False

def main():
    """
    Main function to process the hashprice data and determine the market resolution.
    """
    # Define the timeframe for the market
    start_date = datetime(2025, 5, 19, 18, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))

    # Convert dates to UTC and then to milliseconds since epoch
    start_time_ms = int(start_date.astimezone(timezone.utc).timestamp() * 1000)
    end_time_ms = int(end_date.astimezone(timezone.utc).timestamp() * 1000)

    # Fetch the hashprice data
    data = fetch_hashprice_data(start_time_ms, end_time_ms)

    if data is None:
        logger.error("No data available to process.")
        print("recommendation: p4")
        return

    # Check if the price threshold was exceeded
    if check_price_threshold(data):
        print("recommendation: p2")  # Yes, price reached $57.50001 or higher
    else:
        print("recommendation: p1")  # No, price did not reach $57.50001

if __name__ == "__main__":
    main()