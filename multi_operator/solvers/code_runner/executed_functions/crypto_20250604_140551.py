import requests
import os
from datetime import datetime, timedelta
from pytz import timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants for the API endpoint and the trading pair
DEXSCREENER_API_URL = "https://api.dexscreener.io/latest/dex/tokens/"
HOUSE_SOL_PAIR_ID = "gj5t6kjtw3gww7srmhei1ojckayhyvlwb17gktf96hnh"

def fetch_price_data(start_time, end_time):
    """
    Fetches price data for the HOUSE/SOL trading pair from Dexscreener API within the specified time range.
    
    Args:
        start_time (datetime): Start time for data fetching.
        end_time (datetime): End time for data fetching.
    
    Returns:
        list: List of price data points.
    """
    # Convert datetime to timestamp in milliseconds
    start_timestamp = int(start_time.timestamp() * 1000)
    end_timestamp = int(end_time.timestamp() * 1000)

    # Prepare the API request URL
    url = f"{DEXSCREENER_API_URL}{HOUSE_SOL_PAIR_ID}/candles?from={start_timestamp}&to={end_timestamp}&resolution=1"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data['candles']
    except requests.RequestException as e:
        print(f"Failed to fetch data: {str(e)}")
        return []

def check_price_threshold(candles, threshold=0.200):
    """
    Checks if the price of HOUSE/SOL has reached or exceeded the threshold at any point in the given data.
    
    Args:
        candles (list): List of candle data from Dexscreener.
        threshold (float): Price threshold to check against.
    
    Returns:
        bool: True if the price has reached/exceeded the threshold, False otherwise.
    """
    for candle in candles:
        if float(candle['h']) >= threshold:
            return True
    return False

def main():
    # Define the time range for the query
    et_zone = timezone('US/Eastern')
    start_time = et_zone.localize(datetime(2025, 5, 7, 15, 0, 0))
    end_time = et_zone.localize(datetime(2025, 5, 31, 23, 59, 59))

    # Fetch price data from Dexscreener
    candles = fetch_price_data(start_time, end_time)

    # Check if the price has reached the threshold
    if check_price_threshold(candles):
        print("recommendation: p2")  # Yes, price reached $0.200 or higher
    else:
        print("recommendation: p1")  # No, price did not reach $0.200

if __name__ == "__main__":
    main()