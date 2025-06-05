import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Define the API endpoint for Hyperliquid
HYPERLIQUID_URL = "https://app.hyperliquid.xyz/trade/HYPE/USDC"

def fetch_hyperliquid_data(start_time, end_time):
    """
    Fetches the HYPE/USDC price data from Hyperliquid for the specified time range.
    
    Args:
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.
    
    Returns:
        list: List of price data or None if an error occurs.
    """
    params = {
        'interval': '1m',
        'startTime': start_time,
        'endTime': end_time
    }
    try:
        response = requests.get(HYPERLIQUID_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Failed to fetch data from Hyperliquid: {e}")
        return None

def check_price_dip_to_nine(data):
    """
    Checks if the price dipped to $9.000 or lower in the given data.
    
    Args:
        data (list): List of price data.
    
    Returns:
        bool: True if the price dipped to $9.000 or lower, False otherwise.
    """
    for entry in data:
        if float(entry['L']) <= 9.000:
            return True
    return False

def main():
    # Define the time range
    start_date = datetime(2025, 5, 7, 16, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Convert to UTC and then to milliseconds since epoch
    start_time_utc = start_date.astimezone(pytz.utc)
    end_time_utc = end_date.astimezone(pytz.utc)
    start_time_ms = int(start_time_utc.timestamp() * 1000)
    end_time_ms = int(end_time_utc.timestamp() * 1000)
    
    # Fetch the price data
    price_data = fetch_hyperliquid_data(start_time_ms, end_time_ms)
    
    if price_data is None:
        print("recommendation: p4")  # Unable to fetch data
        return
    
    # Check if the price dipped to $9.000 or lower
    if check_price_dip_to_nine(price_data):
        print("recommendation: p2")  # Yes, it dipped to $9 or lower
    else:
        print("recommendation: p1")  # No, it did not dip to $9 or lower

if __name__ == "__main__":
    main()