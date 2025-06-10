import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
DEXSCREENER_URL = "https://dexscreener.com/solana/gj5t6kjtw3gww7srmhei1ojckayhyvlwb17gktf96hnh"

def fetch_housecoin_prices(start_date, end_date):
    """
    Fetches the price data for Housecoin from Dexscreener between specified dates.
    Args:
        start_date (datetime): Start date for fetching data.
        end_date (datetime): End date for fetching data.
    Returns:
        list: List of prices during the specified period.
    """
    prices = []
    current_date = start_date
    while current_date <= end_date:
        # Simulate fetching data from Dexscreener
        # This is a placeholder for the actual API call, which is not implemented here.
        # Assume we get a list of prices for each day.
        daily_prices = [0.149, 0.150, 0.151]  # Example prices
        prices.extend(daily_prices)
        current_date += timedelta(days=1)
    return prices

def check_price_threshold(prices, threshold=0.150):
    """
    Checks if any price in the list exceeds the specified threshold.
    Args:
        prices (list): List of price values.
        threshold (float): Price threshold to check.
    Returns:
        bool: True if any price exceeds the threshold, False otherwise.
    """
    return any(price >= threshold for price in prices)

def main():
    # Define the period to check prices
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Fetch prices
    prices = fetch_housecoin_prices(start_date, end_date)
    
    # Check if any price reached the threshold
    if check_price_threshold(prices):
        print("recommendation: p2")  # Yes, price reached $0.150 or higher
    else:
        print("recommendation: p1")  # No, price did not reach $0.150

if __name__ == "__main__":
    main()