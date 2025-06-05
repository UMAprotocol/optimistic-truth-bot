import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys are not required for this specific task as we are using a public endpoint
# However, if needed, they can be loaded like this:
# BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

def fetch_fartcoin_prices(start_time, end_time):
    """
    Fetches Fartcoin prices from Dexscreener for a given time range.
    
    Args:
        start_time (datetime): Start time in UTC.
        end_time (datetime): End time in UTC.
    
    Returns:
        list: List of prices within the specified time range.
    """
    url = "https://dexscreener.com/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
    params = {
        "startTime": int(start_time.timestamp() * 1000),
        "endTime": int(end_time.timestamp() * 1000),
        "interval": "1m"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return [float(candle['H']) for candle in data['data']]
    except requests.RequestException as e:
        print(f"Failed to fetch data: {str(e)}")
        return []

def check_price_threshold(prices, threshold=2.5):
    """
    Checks if any price in the list exceeds the given threshold.
    
    Args:
        prices (list): List of float prices.
        threshold (float): Price threshold to check against.
    
    Returns:
        bool: True if any price exceeds the threshold, False otherwise.
    """
    return any(price >= threshold for price in prices)

def main():
    # Define the time range for the query
    start_time = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_time = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Convert time to UTC
    start_time_utc = start_time.astimezone(pytz.utc)
    end_time_utc = end_time.astimezone(pytz.utc)
    
    # Fetch prices
    prices = fetch_fartcoin_prices(start_time_utc, end_time_utc)
    
    # Check if any price exceeds the threshold
    if check_price_threshold(prices):
        print("recommendation: p2")  # Yes, price reached $2.50 or higher
    else:
        print("recommendation: p1")  # No, price did not reach $2.50

if __name__ == "__main__":
    main()