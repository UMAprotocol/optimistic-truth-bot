import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define the API endpoint for Hyperliquid
HYPERLIQUID_API_URL = "https://app.hyperliquid.xyz/trade/HYPE/USDC"

def fetch_hyperliquid_data(start_date, end_date):
    """
    Fetches the 1-minute candle data for the HYPE/USDC pair from Hyperliquid between specified dates.
    
    Args:
        start_date (datetime): Start date and time in UTC.
        end_date (datetime): End date and time in UTC.
    
    Returns:
        list: List of dictionaries containing candle data.
    """
    # Convert datetime to milliseconds since epoch
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)
    
    # Construct the request URL with parameters
    params = {
        "symbol": "HYPEUSDC",
        "interval": "1m",
        "startTime": start_timestamp,
        "endTime": end_timestamp
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
    Checks if the price dipped to $16.000 or lower in the provided data.
    
    Args:
        data (list): List of candle data from Hyperliquid.
    
    Returns:
        bool: True if price dipped to $16.000 or lower, False otherwise.
    """
    for candle in data:
        if float(candle['L']) <= 16.000:
            return True
    return False

def main():
    # Define the time period for the query
    start_date = datetime(2025, 5, 7, 16, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Convert to UTC
    start_date_utc = start_date.astimezone(pytz.utc)
    end_date_utc = end_date.astimezone(pytz.utc)
    
    # Fetch the data from Hyperliquid
    data = fetch_hyperliquid_data(start_date_utc, end_date_utc)
    
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