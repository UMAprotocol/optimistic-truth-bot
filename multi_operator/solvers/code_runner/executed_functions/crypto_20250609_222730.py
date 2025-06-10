import requests
import logging
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Dexscreener for a given cryptocurrency symbol and time range.
    
    Args:
        symbol: Cryptocurrency symbol pair (e.g., 'Fartcoin/SOL')
        start_time: Start time in milliseconds since epoch
        end_time: End time in milliseconds since epoch
    
    Returns:
        List of price data or None if an error occurs
    """
    url = "https://dexscreener.com/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
    params = {
        "symbol": symbol,
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        logger.error(f"Failed to fetch price data: {e}")
        return None

def check_price_dip_to_threshold(price_data, threshold):
    """
    Checks if the price dipped to or below a certain threshold.
    
    Args:
        price_data: List of price data
        threshold: Price threshold to check against
    
    Returns:
        True if price dipped to or below the threshold, False otherwise
    """
    for entry in price_data:
        if entry['L'] <= threshold:
            return True
    return False

def main():
    """
    Main function to process the market resolution based on price data.
    """
    # Define the parameters for the query
    symbol = "Fartcoin/SOL"
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone("US/Eastern"))
    start_time_ms = int(start_date.timestamp() * 1000)
    end_time_ms = int(end_date.timestamp() * 1000)
    threshold_price = 0.20

    # Fetch the price data
    price_data = fetch_price_data(symbol, start_time_ms, end_time_ms)

    if price_data is None:
        logger.error("No price data available, unable to resolve market.")
        print("recommendation: p4")
        return

    # Check if the price dipped to the threshold
    if check_price_dip_to_threshold(price_data, threshold_price):
        print("recommendation: p2")  # Yes, price dipped to $0.20 or lower
    else:
        print("recommendation: p1")  # No, price did not dip to $0.20 or lower

if __name__ == "__main__":
    main()