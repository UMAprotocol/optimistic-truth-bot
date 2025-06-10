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
    Fetches the low prices for the HYPE/USDC trading pair from Hyperliquid between specified dates.
    
    Args:
        start_date (datetime): Start date for the data fetch.
        end_date (datetime): End date for the data fetch.
    
    Returns:
        list: List of low prices or None if an error occurs.
    """
    # Convert dates to timestamps
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)
    
    # Prepare the request parameters
    params = {
        "symbol": "HYPEUSDC",
        "interval": "1m",
        "startTime": start_timestamp,
        "endTime": end_timestamp
    }
    
    try:
        # Make the request to the Hyperliquid API
        response = requests.get(HYPERLIQUID_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract the 'Low' prices from the data
        low_prices = [float(candle['low']) for candle in data]
        return low_prices
    except requests.RequestException as e:
        print(f"Failed to fetch data from Hyperliquid: {e}")
        return None

def check_price_dip_to_nine(low_prices):
    """
    Checks if any of the low prices dips to $9.000 or lower.
    
    Args:
        low_prices (list): List of low prices.
    
    Returns:
        bool: True if any price dips to $9.000 or lower, False otherwise.
    """
    return any(price <= 9.000 for price in low_prices)

def main():
    # Define the time period for the query
    start_date = datetime(2025, 5, 7, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Fetch the low prices from Hyperliquid
    low_prices = fetch_hyperliquid_data(start_date, end_date)
    
    if low_prices is None:
        print("recommendation: p4")  # Unable to fetch data
    else:
        # Check if the price dipped to $9.000 or lower
        if check_price_dip_to_nine(low_prices):
            print("recommendation: p2")  # Yes, price dipped to $9.000 or lower
        else:
            print("recommendation: p1")  # No, price did not dip to $9.000 or lower

if __name__ == "__main__":
    main()