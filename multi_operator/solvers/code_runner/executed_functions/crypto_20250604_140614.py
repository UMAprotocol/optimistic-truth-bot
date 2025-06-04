import requests
import os
from datetime import datetime, timedelta
from pytz import timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants for the API endpoint and the trading pair
DEXSCREENER_API_URL = "https://api.dexscreener.io/latest/dex/tokens"
HOUSE_SOL_PAIR_ID = "gj5t6kjtw3gww7srmhei1ojckayhyvlwb17gktf96hnh"

def fetch_price_data(pair_id, start_time, end_time):
    """
    Fetches price data from Dexscreener for a specific trading pair within a given time range.
    
    Args:
        pair_id (str): The ID of the trading pair on Dexscreener.
        start_time (datetime): Start time for the data fetch.
        end_time (datetime): End time for the data fetch.
    
    Returns:
        list: List of price data points.
    """
    params = {
        "pairAddress": pair_id,
        "from": int(start_time.timestamp()),
        "to": int(end_time.timestamp())
    }
    response = requests.get(DEXSCREENER_API_URL, params=params)
    response.raise_for_status()
    data = response.json()
    return data['pairs'][0]['candles']

def check_price_threshold(candles, threshold=0.200):
    """
    Checks if the price in any candle has reached or exceeded the threshold.
    
    Args:
        candles (list): List of candle data.
        threshold (float): Price threshold to check against.
    
    Returns:
        bool: True if threshold is met or exceeded, False otherwise.
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

    # Fetch the price data
    try:
        candles = fetch_price_data(HOUSE_SOL_PAIR_ID, start_time, end_time)
        # Check if the price has reached the threshold
        if check_price_threshold(candles):
            print("recommendation: p2")  # Yes, price reached $0.200 or higher
        else:
            print("recommendation: p1")  # No, price did not reach $0.200
    except Exception as e:
        print(f"An error occurred: {e}")
        print("recommendation: p4")  # Unable to determine due to error

if __name__ == "__main__":
    main()