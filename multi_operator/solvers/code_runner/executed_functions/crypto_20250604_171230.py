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
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.

    Returns:
        list: List of candle data where each candle is a list.
    """
    params = {
        "symbol": "HYPEUSDC",
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        response = requests.get(HYPERLIQUID_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Failed to fetch data from Hyperliquid: {e}")
        return None

def check_price_dip_to_nine(data):
    """
    Checks if the price dipped to $9.000 or lower in the provided candle data.

    Args:
        data (list): List of candle data.

    Returns:
        bool: True if price dipped to $9.000 or lower, False otherwise.
    """
    for candle in data:
        if float(candle['L']) <= 9.000:
            return True
    return False

def main():
    # Define the time range for the query
    start_date = datetime(2025, 5, 7, 16, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))

    # Convert datetime to milliseconds since epoch
    start_time_ms = int(start_date.timestamp() * 1000)
    end_time_ms = int(end_date.timestamp() * 1000)

    # Fetch the candle data from Hyperliquid
    data = fetch_hyperliquid_data(start_time_ms, end_time_ms)

    # Check if the price dipped to $9.000 or lower
    if data and check_price_dip_to_nine(data):
        print("recommendation: p2")  # Yes, price dipped to $9 or lower
    else:
        print("recommendation: p1")  # No, price did not dip to $9 or lower

if __name__ == "__main__":
    main()