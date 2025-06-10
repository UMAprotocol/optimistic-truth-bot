import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define the API endpoint for Hyperliquid
HYPERLIQUID_ENDPOINT = "https://app.hyperliquid.xyz/trade/HYPE/USDC"

def fetch_hyperliquid_data(start_time, end_time):
    """
    Fetches the HYPE/USDC 'L' prices from Hyperliquid within the specified time range.
    
    Args:
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.
    
    Returns:
        list: List of prices or None if an error occurs.
    """
    params = {
        "symbol": "HYPEUSDC",
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        response = requests.get(HYPERLIQUID_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()
        return [float(candle['l']) for candle in data]  # Assuming 'l' is the key for low prices
    except Exception as e:
        print(f"Failed to fetch data from Hyperliquid: {e}")
        return None

def check_price_dip_to_20(prices):
    """
    Checks if any price in the list dips to $20.000 or lower.
    
    Args:
        prices (list): List of prices.
    
    Returns:
        bool: True if any price dips to $20.000 or lower, False otherwise.
    """
    return any(price <= 20.000 for price in prices)

def main():
    # Define the time range
    start_date = datetime(2025, 5, 7, 16, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Convert to UTC and then to milliseconds since epoch
    start_time_utc = start_date.astimezone(pytz.utc)
    end_time_utc = end_date.astimezone(pytz.utc)
    start_time_ms = int(start_time_utc.timestamp() * 1000)
    end_time_ms = int(end_time_utc.timestamp() * 1000)
    
    # Fetch the price data
    prices = fetch_hyperliquid_data(start_time_ms, end_time_ms)
    
    if prices is None:
        print("recommendation: p4")  # Unable to fetch data
    elif check_price_dip_to_20(prices):
        print("recommendation: p2")  # Yes, price dipped to $20 or lower
    else:
        print("recommendation: p1")  # No, price did not dip to $20 or lower

if __name__ == "__main__":
    main()