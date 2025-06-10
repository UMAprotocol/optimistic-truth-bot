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
        pair_id: The ID of the trading pair on Dexscreener.
        start_time: Start time in UTC as datetime object.
        end_time: End time in UTC as datetime object.
    
    Returns:
        JSON response containing candle data.
    """
    url = f"https://api.dexscreener.io/latest/dex/candles/{pair_id}"
    params = {
        "from": int(start_time.timestamp()),
        "to": int(end_time.timestamp()),
        "resolution": "1m"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def check_price_dip_to_threshold(candles, threshold):
    """
    Checks if the 'L' price in any candle dipped to or below the threshold.
    
    Args:
        candles: List of candle data from Dexscreener.
        threshold: Price threshold to check against.
    
    Returns:
        True if any 'L' price is <= threshold, otherwise False.
    """
    for candle in candles:
        if float(candle['l']) <= threshold:
            return True
    return False

def main():
    # Define the trading pair ID and threshold from the problem statement
    pair_id = "bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
    threshold_price = 0.60
    start_time_et = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_time_et = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Convert Eastern Time to UTC
    start_time_utc = start_time_et.astimezone(pytz.utc)
    end_time_utc = end_time_et.astimezone(pytz.utc)
    
    try:
        # Fetch candle data from Dexscreener
        data = fetch_dexscreener_data(pair_id, start_time_utc, end_time_utc)
        candles = data['data']['candles']
        
        # Check if the price dipped to or below the threshold
        if check_price_dip_to_threshold(candles, threshold_price):
            print("recommendation: p2")  # Yes, price dipped to $0.60 or lower
        else:
            print("recommendation: p1")  # No, price did not dip to $0.60 or lower
    except Exception as e:
        print(f"Error occurred: {e}")
        print("recommendation: p4")  # Unable to determine due to an error

if __name__ == "__main__":
    main()