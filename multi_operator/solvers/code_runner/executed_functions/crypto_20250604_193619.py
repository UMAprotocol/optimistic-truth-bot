import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Define the API endpoint for Hyperliquid
HYPERLIQUID_URL = "https://app.hyperliquid.xyz/trade/HYPE/USDC"

def fetch_hyperliquid_data(start_date, end_date):
    """
    Fetches the 1-minute candle data for HYPE/USDC from Hyperliquid within the specified date range.
    
    Args:
        start_date (datetime): Start date of the data fetching period.
        end_date (datetime): End date of the data fetching period.
    
    Returns:
        list: List of dictionaries containing candle data.
    """
    # Convert datetime to timestamps for the API
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)
    
    # Construct the API URL with parameters
    params = {
        "symbol": "HYPEUSDC",
        "interval": "1m",
        "startTime": start_timestamp,
        "endTime": end_timestamp
    }
    
    try:
        response = requests.get(HYPERLIQUID_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Failed to fetch data from Hyperliquid: {e}")
        return None

def check_price_dip_to_14(data):
    """
    Checks if the price dipped to $14.000 or lower in the provided data.
    
    Args:
        data (list): List of candle data from Hyperliquid.
    
    Returns:
        bool: True if price dipped to $14.000 or lower, False otherwise.
    """
    for candle in data:
        if float(candle['L']) <= 14.000:
            return True
    return False

def main():
    # Define the time period for the query
    start_date = datetime(2025, 5, 7, 16, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Fetch the data from Hyperliquid
    data = fetch_hyperliquid_data(start_date, end_date)
    
    # Check if the price dipped to $14.000 or lower
    if data and check_price_dip_to_14(data):
        print("recommendation: p2")  # Yes, price dipped to $14 or lower
    else:
        print("recommendation: p1")  # No, price did not dip to $14 or lower

if __name__ == "__main__":
    main()