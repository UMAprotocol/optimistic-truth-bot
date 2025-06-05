import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Define the API endpoint for Hyperliquid
HYPERLIQUID_API_URL = "https://app.hyperliquid.xyz/trade/HYPE/USDC"

def fetch_hyperliquid_data(start_time, end_time):
    """
    Fetches the 1-minute candle data for HYPE/USDC from Hyperliquid within the specified time range.

    Args:
        start_time (datetime): Start time in UTC.
        end_time (datetime): End time in UTC.

    Returns:
        list: List of candle data where each candle is a dictionary.
    """
    params = {
        "interval": "1m",
        "startTime": int(start_time.timestamp() * 1000),  # Convert to milliseconds
        "endTime": int(end_time.timestamp() * 1000)       # Convert to milliseconds
    }
    try:
        response = requests.get(HYPERLIQUID_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Failed to fetch data from Hyperliquid: {e}")
        return None

def check_price_dip_to_16(data):
    """
    Checks if the price dipped to $16.000 or lower in the provided candle data.

    Args:
        data (list): List of candle data.

    Returns:
        bool: True if price dipped to $16.000 or lower, False otherwise.
    """
    for candle in data:
        if float(candle['L']) <= 16.000:
            return True
    return False

def main():
    # Define the time range for the query
    start_time = datetime(2025, 5, 7, 16, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_time = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))

    # Convert time to UTC
    start_time_utc = start_time.astimezone(pytz.utc)
    end_time_utc = end_time.astimezone(pytz.utc)

    # Fetch the candle data from Hyperliquid
    data = fetch_hyperliquid_data(start_time_utc, end_time_utc)

    if data is None:
        print("recommendation: p4")  # Unable to fetch data
    else:
        # Check if the price dipped to $16.000 or lower
        if check_price_dip_to_16(data):
            print("recommendation: p2")  # Yes
        else:
            print("recommendation: p1")  # No

if __name__ == "__main__":
    main()