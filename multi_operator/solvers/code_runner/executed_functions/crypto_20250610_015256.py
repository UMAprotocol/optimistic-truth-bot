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
        return [float(candle['L']) for candle in data]
    except Exception as e:
        print(f"Failed to fetch data from Hyperliquid: {e}")
        return None

def check_price_dip_to_threshold(prices, threshold):
    """
    Checks if any price in the list dips to or below the threshold.
    
    Args:
        prices (list): List of prices.
        threshold (float): Threshold price to check against.
    
    Returns:
        bool: True if any price dips to or below the threshold, False otherwise.
    """
    return any(price <= threshold for price in prices)

def main():
    # Define the time range and threshold for checking the price dip
    start_date = datetime(2025, 5, 7, 16, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    threshold_price = 20.0

    # Convert datetime to milliseconds since epoch
    start_time_ms = int(start_date.timestamp() * 1000)
    end_time_ms = int(end_date.timestamp() * 1000)

    # Fetch the price data from Hyperliquid
    prices = fetch_hyperliquid_data(start_time_ms, end_time_ms)

    if prices is None:
        print("recommendation: p4")  # Unable to resolve due to data fetch failure
    else:
        # Check if the price dipped to or below the threshold
        if check_price_dip_to_threshold(prices, threshold_price):
            print("recommendation: p2")  # Yes, price dipped to $20 or below
        else:
            print("recommendation: p1")  # No, price did not dip to $20 or below

if __name__ == "__main__":
    main()