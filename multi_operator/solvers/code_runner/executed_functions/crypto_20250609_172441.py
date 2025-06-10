import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define the API endpoint for Hyperliquid
HYPERLIQUID_URL = "https://app.hyperliquid.xyz/trade/HYPE/USDC"

def fetch_hyperliquid_data(start_date, end_date):
    """
    Fetches the 1-minute candle "L" prices for HYPE/USDC from Hyperliquid within a specified date range.
    
    Args:
        start_date (datetime): Start date and time in UTC.
        end_date (datetime): End date and time in UTC.
    
    Returns:
        list: List of prices or None if an error occurs.
    """
    # Convert datetime to milliseconds since epoch
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)
    
    # Construct the request URL
    url = f"{HYPERLIQUID_URL}?symbol=HYPEUSDC&interval=1m&startTime={start_timestamp}&endTime={end_timestamp}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        # Assuming the API returns a list of candles where each candle is a dictionary
        # and 'L' price is accessible via key 'low'
        prices = [float(candle['low']) for candle in data]
        return prices
    except Exception as e:
        print(f"Failed to fetch data from Hyperliquid: {e}")
        return None

def check_price_dip_to_10(prices):
    """
    Checks if any price in the list dips to $10.000 or lower.
    
    Args:
        prices (list): List of prices.
    
    Returns:
        bool: True if any price is $10.000 or lower, False otherwise.
    """
    return any(price <= 10.000 for price in prices)

def main():
    # Define the time range for the query
    start_date = datetime(2025, 5, 7, 16, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Convert time zone to UTC
    start_date_utc = start_date.astimezone(pytz.utc)
    end_date_utc = end_date.astimezone(pytz.utc)
    
    # Fetch the price data
    prices = fetch_hyperliquid_data(start_date_utc, end_date_utc)
    
    if prices is not None:
        # Check if the price dipped to $10.000 or lower
        if check_price_dip_to_10(prices):
            print("recommendation: p2")  # Yes, it dipped to $10 or lower
        else:
            print("recommendation: p1")  # No, it did not dip to $10 or lower
    else:
        print("recommendation: p4")  # Unable to determine due to data fetch failure

if __name__ == "__main__":
    main()