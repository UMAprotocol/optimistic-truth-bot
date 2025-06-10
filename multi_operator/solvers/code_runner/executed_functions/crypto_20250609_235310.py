import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Constants for the API endpoints
DEXSCREENER_API_URL = "https://api.dexscreener.io/latest/dex/pairs/solana/gj5t6kjtw3gww7srmhei1ojckayhyvlwb17gktf96hnh"

def fetch_dexscreener_data():
    """
    Fetches the historical price data for the HOUSE/SOL pair from Dexscreener.
    """
    try:
        response = requests.get(DEXSCREENER_API_URL)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Failed to fetch data from Dexscreener: {e}")
        return None

def check_price_threshold(data, start_time, end_time, price_threshold=0.30000):
    """
    Checks if the price of HOUSE/SOL ever reached or exceeded the threshold between the specified times.
    
    Args:
        data: The JSON data from Dexscreener.
        start_time: The start datetime object.
        end_time: The end datetime object.
        price_threshold: The price threshold to check against.
    
    Returns:
        True if the price reached or exceeded the threshold, False otherwise.
    """
    if not data or 'pair' not in data or 'chartData' not in data['pair']:
        print("Invalid data format or data is missing.")
        return False

    for candle in data['pair']['chartData']:
        candle_time = datetime.fromtimestamp(candle['time'] / 1000, tz=pytz.UTC)
        if start_time <= candle_time <= end_time:
            if candle['h'] >= price_threshold:
                return True
    return False

def main():
    # Define the time range and price threshold based on the ancillary data
    start_time = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_time = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    price_threshold = 0.30000

    # Fetch data from Dexscreener
    data = fetch_dexscreener_data()

    # Check if the price threshold was ever met or exceeded
    if check_price_threshold(data, start_time, end_time, price_threshold):
        print("recommendation: p2")  # Yes, price reached $0.30000 or higher
    else:
        print("recommendation: p1")  # No, price did not reach $0.30000

if __name__ == "__main__":
    main()