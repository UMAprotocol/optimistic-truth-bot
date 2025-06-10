import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

def fetch_dexscreener_data(pair_id="gj5t6kjtw3gww7srmhei1ojckayhyvlwb17gktf96hnh", interval="1m"):
    """
    Fetches historical price data for a specific trading pair from Dexscreener.
    
    Args:
        pair_id (str): The ID of the trading pair on Dexscreener.
        interval (str): The interval for the candle data.
    
    Returns:
        list: A list of candle data.
    """
    url = f"https://api.dexscreener.io/latest/dex/pairs/solana/{pair_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        candles = data['pair']['candles'][interval]
        return candles
    except Exception as e:
        print(f"Failed to fetch data from Dexscreener: {e}")
        return None

def check_price_dip_to_threshold(candles, threshold=0.025):
    """
    Checks if the price in any candle dipped to or below the threshold.
    
    Args:
        candles (list): List of candle data.
        threshold (float): The price threshold to check against.
    
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
    
    # Convert to UTC as Dexscreener API uses UTC
    start_date_utc = start_date.astimezone(pytz.utc)
    end_date_utc = end_date.astimezone(pytz.utc)
    
    # Fetch candle data from Dexscreener
    candles = fetch_dexscreener_data()
    
    if candles is None:
        print("recommendation: p4")  # Unable to resolve due to data fetch failure
        return
    
    # Check if the price dipped to $0.025 or lower
    price_dipped = check_price_dip_to_threshold(candles)
    
    if price_dipped:
        print("recommendation: p2")  # Yes, price dipped to $0.025 or lower
    else:
        print("recommendation: p1")  # No, price did not dip to $0.025 or lower

if __name__ == "__main__":
    main()