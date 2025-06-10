import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define the URL for the Hyperliquid API
HYPERLIQUID_URL = "https://app.hyperliquid.xyz/trade/HYPE/USDC"

def fetch_hyperliquid_data(start_date, end_date):
    """
    Fetches the HYPE/USDC 'L' prices from Hyperliquid between specified dates.
    
    Args:
        start_date (datetime): Start date and time in ET timezone.
        end_date (datetime): End date and time in ET timezone.
    
    Returns:
        list: List of prices or None if no data could be fetched.
    """
    # Convert dates to UTC for the API request
    start_date_utc = start_date.astimezone(pytz.utc)
    end_date_utc = end_date.astimezone(pytz.utc)

    # Format timestamps for the API
    start_timestamp = int(start_date_utc.timestamp() * 1000)
    end_timestamp = int(end_date_utc.timestamp() * 1000)

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
        # Extract the 'L' prices from the data
        prices = [float(item['L']) for item in data]
        return prices
    except Exception as e:
        print(f"Failed to fetch data from Hyperliquid: {e}")
        return None

def check_price_dip_to_20(prices):
    """
    Checks if any price in the list dips to $20.000 or lower.
    
    Args:
        prices (list): List of prices.
    
    Returns:
        bool: True if any price is $20.000 or lower, False otherwise.
    """
    return any(price <= 20.000 for price in prices)

def main():
    # Define the time period in ET timezone
    et_timezone = pytz.timezone('US/Eastern')
    start_date = et_timezone.localize(datetime(2025, 5, 7, 16, 0, 0))
    end_date = et_timezone.localize(datetime(2025, 5, 31, 23, 59, 59))

    # Fetch the price data
    prices = fetch_hyperliquid_data(start_date, end_date)

    if prices is not None:
        # Check if the price dipped to $20.000 or lower
        if check_price_dip_to_20(prices):
            print("recommendation: p2")  # Yes, it dipped to $20 or lower
        else:
            print("recommendation: p1")  # No, it did not dip to $20 or lower
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data fetch failure

if __name__ == "__main__":
    main()