import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Define the API endpoint for Hyperliquid
HYPERLIQUID_ENDPOINT = "https://app.hyperliquid.xyz/trade/HYPE/USDC"

def fetch_hyperliquid_data(start_time, end_time):
    """
    Fetches the 1-minute candle data for HYPE/USDC from Hyperliquid within the specified time range.

    Args:
        start_time (datetime): Start time for data fetching.
        end_time (datetime): End time for data fetching.

    Returns:
        list: List of candle data where each candle is a dictionary.
    """
    # Convert datetime to timestamps in milliseconds
    start_timestamp = int(start_time.timestamp() * 1000)
    end_timestamp = int(end_time.timestamp() * 1000)

    # Prepare the request parameters
    params = {
        "symbol": "HYPEUSDC",
        "interval": "1m",
        "startTime": start_timestamp,
        "endTime": end_timestamp
    }

    try:
        # Send the request to Hyperliquid
        response = requests.get(HYPERLIQUID_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Failed to fetch data from Hyperliquid: {e}")
        return None

def check_price_dip_to_twelve(data):
    """
    Checks if the price dipped to $12.000 or lower in the provided candle data.

    Args:
        data (list): List of candle data.

    Returns:
        bool: True if price dipped to $12.000 or lower, False otherwise.
    """
    for candle in data:
        if float(candle['L']) <= 12.000:
            return True
    return False

def main():
    # Define the time range for the query
    start_time = datetime(2025, 5, 7, 16, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_time = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))

    # Fetch the candle data from Hyperliquid
    candle_data = fetch_hyperliquid_data(start_time, end_time)

    if candle_data is not None:
        # Check if the price dipped to $12.000 or lower
        if check_price_dip_to_twelve(candle_data):
            print("recommendation: p2")  # Yes, price dipped to $12 or lower
        else:
            print("recommendation: p1")  # No, price did not dip to $12 or lower
    else:
        print("recommendation: p4")  # Unable to determine due to data fetch failure

if __name__ == "__main__":
    main()