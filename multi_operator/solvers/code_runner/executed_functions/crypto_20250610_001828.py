import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants for the API endpoints
HYPERLIQUID_URL = "https://app.hyperliquid.xyz/trade/HYPE/USDC"

def fetch_hyperliquid_data(start_date, end_date):
    """
    Fetches the HYPE/USDC price data from Hyperliquid between specified dates.
    Args:
        start_date (datetime): Start date of the period to fetch data for.
        end_date (datetime): End date of the period to fetch data for.
    Returns:
        list: List of price data where each item is a dictionary with 'L' price.
    """
    # Convert datetime to timestamps for the API
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)

    # Construct the URL with the required parameters
    url = f"{HYPERLIQUID_URL}?symbol=HYPEUSDC&interval=1m&startTime={start_timestamp}&endTime={end_timestamp}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Failed to fetch data from Hyperliquid: {e}")
        return None

def check_price_dip_to_threshold(prices, threshold):
    """
    Checks if the price dipped to or below the threshold at any point.
    Args:
        prices (list): List of price data.
        threshold (float): Price threshold to check.
    Returns:
        bool: True if price dipped to or below the threshold, False otherwise.
    """
    for price_data in prices:
        if price_data['L'] <= threshold:
            return True
    return False

def main():
    # Define the time period and threshold
    start_date = datetime(2025, 5, 7, 16, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    threshold_price = 18.0

    # Fetch the price data from Hyperliquid
    prices = fetch_hyperliquid_data(start_date, end_date)

    # Check if the price dipped to or below the threshold
    if prices and check_price_dip_to_threshold(prices, threshold_price):
        print("recommendation: p2")  # Yes, price dipped to $18 or lower
    else:
        print("recommendation: p1")  # No, price did not dip to $18 or lower

if __name__ == "__main__":
    main()