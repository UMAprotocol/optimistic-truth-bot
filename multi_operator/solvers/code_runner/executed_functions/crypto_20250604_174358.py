import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Constants for the API endpoint and the specific trading pair
DEXSCREENER_URL = "https://dexscreener.com/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
TRADING_PAIR = "Fartcoin/SOL"

def fetch_dexscreener_data(start_date, end_date):
    """
    Fetches trading data from Dexscreener for a specific trading pair within a given date range.
    
    Args:
        start_date (datetime): Start date for the data fetch.
        end_date (datetime): End date for the data fetch.
    
    Returns:
        list: List of dictionaries containing trading data.
    """
    # Convert datetime to timestamps for the API call
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())

    # Construct the API URL with parameters
    url = f"{DEXSCREENER_URL}?pair={TRADING_PAIR}&interval=1m&start={start_timestamp}&end={end_timestamp}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Failed to fetch data from Dexscreener: {e}")
        return None

def check_price_dip_to_target(data, target_price=0.90):
    """
    Checks if the price dipped to or below the target price in the fetched data.
    
    Args:
        data (list): List of trading data.
        target_price (float): Target price to check against.
    
    Returns:
        bool: True if price dipped to or below the target, False otherwise.
    """
    for entry in data:
        if float(entry['L']) <= target_price:
            return True
    return False

def main():
    # Define the date range for the query
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))

    # Fetch the data from Dexscreener
    data = fetch_dexscreener_data(start_date, end_date)

    # Check if the price dipped to $0.90 or below
    if data and check_price_dip_to_target(data):
        print("recommendation: p2")  # Yes, price dipped to $0.90 or below
    else:
        print("recommendation: p1")  # No, price did not dip to $0.90 or below

if __name__ == "__main__":
    main()