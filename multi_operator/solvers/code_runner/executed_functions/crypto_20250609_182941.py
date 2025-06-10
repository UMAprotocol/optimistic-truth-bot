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

def check_price_dip_to_threshold(candles, threshold):
    """
    Checks if the price in any candle dipped to or below the threshold.
    
    Args:
        candles (list): List of candle data.
        threshold (float): Price threshold to check.
    
    Returns:
        bool: True if price dipped to or below the threshold, False otherwise.
    """
    for candle in candles:
        if float(candle['l']) <= threshold:
            return True
    return False

def main():
    # Define the trading pair ID and threshold from the problem statement
    pair_id = "bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
    threshold = 0.60
    start_time = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_time = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Fetch the candle data from Dexscreener
    candles = fetch_dexscreener_data(pair_id, start_time, end_time)
    
    if candles is None:
        print("recommendation: p4")  # Unable to resolve due to data fetch failure
        return
    
    # Check if the price dipped to the threshold
    if check_price_dip_to_threshold(candles, threshold):
        print("recommendation: p2")  # Yes, price dipped to $0.60 or lower
    else:
        print("recommendation: p1")  # No, price did not dip to $0.60 or lower

if __name__ == "__main__":
    main()