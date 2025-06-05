import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

def fetch_dexscreener_data(pair_id, start_time, end_time):
    """
    Fetches the 1-minute candle data for a specific trading pair from Dexscreener.
    
    Args:
        pair_id (str): The ID of the trading pair on Dexscreener.
        start_time (datetime): Start time for data fetching.
        end_time (datetime): End time for data fetching.
    
    Returns:
        list: List of candle data or None if an error occurs.
    """
    url = f"https://api.dexscreener.io/latest/dex/candles/{pair_id}"
    params = {
        "from": int(start_time.timestamp()),
        "to": int(end_time.timestamp()),
        "resolution": "1m"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data['candles']
    except Exception as e:
        print(f"Failed to fetch data from Dexscreener: {e}")
        return None

def check_price_threshold(candles, threshold=2.5):
    """
    Checks if any candle's high price meets or exceeds the threshold.
    
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
    # Define the trading pair ID and the time period for the query
    pair_id = "bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
    start_time = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_time = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Fetch the candle data from Dexscreener
    candles = fetch_dexscreener_data(pair_id, start_time, end_time)
    
    if candles is None:
        print("recommendation: p4")  # Unable to resolve due to data fetch failure
        return
    
    # Check if the price threshold was ever met or exceeded
    if check_price_threshold(candles):
        print("recommendation: p2")  # Yes, price reached $2.50 or higher
    else:
        print("recommendation: p1")  # No, price did not reach $2.50

if __name__ == "__main__":
    main()