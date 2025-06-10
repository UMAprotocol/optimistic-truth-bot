import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Constants for the API endpoint and the HOUSE/SOL trading pair
DEXSCREENER_API_URL = "https://api.dexscreener.io/latest/dex/tokens/gj5t6kjtw3gww7srmhei1ojckayhyvlwb17gktf96hnh"

def fetch_data(start_time, end_time):
    """
    Fetches the price data for HOUSE/SOL from Dexscreener API within the specified time range.
    
    Args:
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.
    
    Returns:
        list: List of price data or None if an error occurs.
    """
    try:
        response = requests.get(DEXSCREENER_API_URL, params={"from": start_time, "to": end_time})
        response.raise_for_status()
        data = response.json()
        return data['pairs'][0]['candles']
    except Exception as e:
        print(f"Failed to fetch data: {e}")
        return None

def check_price_dip_to_threshold(candles, threshold=0.02000):
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
    start_time_utc = start_date.astimezone(pytz.utc)
    end_time_utc = end_date.astimezone(pytz.utc)
    start_time_ms = int(start_time_utc.timestamp() * 1000)
    end_time_ms = int(end_time_utc.timestamp() * 1000)
    
    # Fetch the price data
    candles = fetch_data(start_time_ms, end_time_ms)
    
    if candles is None:
        print("recommendation: p4")  # Unable to resolve due to data fetch failure
        return
    
    # Check if the price dipped to $0.02000 or lower
    if check_price_dip_to_threshold(candles):
        print("recommendation: p2")  # Yes, price dipped to $0.02000 or lower
    else:
        print("recommendation: p1")  # No, price did not dip to $0.02000 or lower

if __name__ == "__main__":
    main()