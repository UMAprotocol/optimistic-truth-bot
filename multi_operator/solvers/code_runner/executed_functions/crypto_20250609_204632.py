import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Constants for the API endpoint and the trading pair ID
DEXSCREENER_API_URL = "https://api.dexscreener.io/latest/dex/candles"
PAIR_ID = "bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"

def fetch_candles(start_time, end_time):
    """
    Fetches 1-minute candle data from Dexscreener for the specified time range.
    
    Args:
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.
    
    Returns:
        list: List of candle data where each candle is a dictionary.
    """
    params = {
        "pairAddress": PAIR_ID,
        "interval": "1m",
        "start": start_time,
        "end": end_time
    }
    try:
        response = requests.get(DEXSCREENER_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data['candles']
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return None

def check_price_dip(candles, threshold):
    """
    Checks if the price dipped to or below the threshold in any of the candles.
    
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
    # Define the time range for the query
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Convert to UTC and then to milliseconds since epoch
    start_utc = start_date.astimezone(pytz.utc)
    end_utc = end_date.astimezone(pytz.utc)
    start_ms = int(start_utc.timestamp() * 1000)
    end_ms = int(end_utc.timestamp() * 1000)
    
    # Fetch candle data
    candles = fetch_candles(start_ms, end_ms)
    
    if candles is None:
        print("recommendation: p4")  # Unable to fetch data
        return
    
    # Check if the price dipped to $0.85 or below
    if check_price_dip(candles, 0.85):
        print("recommendation: p2")  # Yes, price dipped to $0.85 or below
    else:
        print("recommendation: p1")  # No, price did not dip to $0.85 or below

if __name__ == "__main__":
    main()