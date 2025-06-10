import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for the API and the market conditions
HYPERLIQUID_BASE_URL = "https://app.hyperliquid.xyz/trade/HYPE/USDC"
TIMEZONE = "US/Eastern"
START_DATE = "2025-05-07 16:00:00"
END_DATE = "2025-05-31 23:59:00"
TARGET_PRICE = 18.0

def fetch_hyperliquid_data(start_time, end_time):
    """
    Fetches the HYPE/USDC price data from Hyperliquid within the specified time range.
    Args:
        start_time (datetime): Start time for data fetching.
        end_time (datetime): End time for data fetching.
    Returns:
        list: List of price data.
    """
    # Convert times to the appropriate format for the API
    start_timestamp = int(start_time.timestamp() * 1000)
    end_timestamp = int(end_time.timestamp() * 1000)
    
    # Construct the API URL
    url = f"{HYPERLIQUID_BASE_URL}?symbol=HYPEUSDC&interval=1m&startTime={start_timestamp}&endTime={end_timestamp}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        logging.error(f"Failed to fetch data from Hyperliquid: {e}")
        return None

def check_price_dip_to_target(data, target_price):
    """
    Checks if the price dipped to or below the target price.
    Args:
        data (list): List of price data.
        target_price (float): Target price to check against.
    Returns:
        bool: True if price dipped to or below target, False otherwise.
    """
    for entry in data:
        if float(entry['L']) <= target_price:
            return True
    return False

def main():
    # Convert string dates to datetime objects
    tz = pytz.timezone(TIMEZONE)
    start_time = tz.localize(datetime.strptime(START_DATE, "%Y-%m-%d %H:%M:%S"))
    end_time = tz.localize(datetime.strptime(END_DATE, "%Y-%m-%d %H:%M:%S"))
    
    # Fetch the price data
    data = fetch_hyperliquid_data(start_time, end_time)
    
    if data is None:
        print("recommendation: p4")  # Unable to fetch data
        return
    
    # Check if the price dipped to or below the target price
    if check_price_dip_to_target(data, TARGET_PRICE):
        print("recommendation: p2")  # Yes, price dipped to or below $18
    else:
        print("recommendation: p1")  # No, price did not dip to or below $18

if __name__ == "__main__":
    main()