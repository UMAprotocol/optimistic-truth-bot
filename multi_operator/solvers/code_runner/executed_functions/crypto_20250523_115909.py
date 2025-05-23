import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Define the API endpoints
HYPERLIQUID_URL = "https://app.hyperliquid.xyz/trade/HYPE/USDC"

def fetch_hyperliquid_data(start_time, end_time):
    """
    Fetches the high prices of HYPE/USDC from Hyperliquid within the specified timeframe.
    
    Args:
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.
    
    Returns:
        list: List of high prices or None if an error occurs.
    """
    params = {
        "symbol": "HYPEUSDC",
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        response = requests.get(HYPERLIQUID_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return [float(candle[2]) for candle in data]  # Assuming the high price is at index 2
    except Exception as e:
        print(f"Failed to fetch data from Hyperliquid: {e}")
        return None

def check_price_threshold(prices, threshold):
    """
    Checks if any price in the list exceeds the given threshold.
    
    Args:
        prices (list): List of float prices.
        threshold (float): Price threshold to check against.
    
    Returns:
        bool: True if any price exceeds the threshold, False otherwise.
    """
    return any(price >= threshold for price in prices)

def main():
    # Define the time range for the query
    start_date = datetime(2025, 5, 7, 16, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone("US/Eastern"))
    
    # Convert to UTC and then to milliseconds since epoch
    start_time_utc = int(start_date.astimezone(pytz.utc).timestamp() * 1000)
    end_time_utc = int(end_date.astimezone(pytz.utc).timestamp() * 1000)
    
    # Fetch the high prices from Hyperliquid
    high_prices = fetch_hyperliquid_data(start_time_utc, end_time_utc)
    
    if high_prices is None:
        print("recommendation: p4")  # Unable to fetch data
    elif check_price_threshold(high_prices, 35.0):
        print("recommendation: p2")  # Yes, price reached $35 or higher
    else:
        print("recommendation: p1")  # No, price did not reach $35

if __name__ == "__main__":
    main()