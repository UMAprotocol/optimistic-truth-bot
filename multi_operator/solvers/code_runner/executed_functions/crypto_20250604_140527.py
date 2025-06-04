import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Constants for the API endpoint and the trading pair
DEXSCREENER_API_URL = "https://api.dexscreener.io/latest/dex/candles"
TRADING_PAIR_ID = "gj5t6kjtw3gww7srmhei1ojckayhyvlwb17gktf96hnh"  # HOUSE/SOL pair ID

def fetch_candles(start_time, end_time):
    """
    Fetches 1-minute candles from Dexscreener for the HOUSE/SOL trading pair within the specified time range.
    
    Args:
        start_time (int): Start time in milliseconds since the epoch.
        end_time (int): End time in milliseconds since the epoch.
    
    Returns:
        list: List of candle data.
    """
    params = {
        "pairAddress": TRADING_PAIR_ID,
        "from": start_time,
        "to": end_time,
        "limit": 1000,  # Adjust based on the maximum allowed by the API
        "interval": "1m"
    }
    response = requests.get(DEXSCREENER_API_URL, params=params)
    response.raise_for_status()
    data = response.json()
    return data['candles']

def check_price_threshold(candles, threshold=0.200):
    """
    Checks if any candle in the list has a closing price ('H' price) that meets or exceeds the threshold.
    
    Args:
        candles (list): List of candle data.
        threshold (float): Price threshold to check against.
    
    Returns:
        bool: True if the threshold is met or exceeded, False otherwise.
    """
    for candle in candles:
        if float(candle['h']) >= threshold:
            return True
    return False

def main():
    # Define the time range for the query
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Convert to UTC and then to milliseconds since epoch
    start_date_utc = start_date.astimezone(pytz.utc)
    end_date_utc = end_date.astimezone(pytz.utc)
    start_time_ms = int(start_date_utc.timestamp() * 1000)
    end_time_ms = int(end_date_utc.timestamp() * 1000)
    
    try:
        # Fetch candles from Dexscreener
        candles = fetch_candles(start_time_ms, end_time_ms)
        
        # Check if any candle meets the price threshold
        if check_price_threshold(candles):
            print("recommendation: p2")  # Yes, price reached $0.200 or higher
        else:
            print("recommendation: p1")  # No, price did not reach $0.200
    except Exception as e:
        print(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()