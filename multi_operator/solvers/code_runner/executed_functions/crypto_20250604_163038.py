import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

def fetch_dexscreener_data(pair_id, start_time, end_time):
    """
    Fetch historical data from Dexscreener for a specific trading pair within a given time range.
    
    Args:
        pair_id (str): The ID of the trading pair on Dexscreener.
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.
    
    Returns:
        list: List of historical data points.
    """
    url = f"https://io.dexscreener.io/u/trading-pairs/{pair_id}/candles"
    params = {
        'from': start_time,
        'to': end_time,
        'resolution': '1m'  # 1 minute resolution
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data['candles']
    except requests.RequestException as e:
        print(f"Failed to fetch data from Dexscreener: {e}")
        return None

def check_price_dip_to_target(candles, target_price):
    """
    Check if the price dipped to or below the target price in any of the provided candles.
    
    Args:
        candles (list): List of candle data from Dexscreener.
        target_price (float): Target price to check against.
    
    Returns:
        bool: True if the price dipped to or below the target price, False otherwise.
    """
    for candle in candles:
        if float(candle['l']) <= target_price:
            return True
    return False

def main():
    # Define the trading pair ID and target price
    pair_id = "bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
    target_price = 0.75

    # Define the time range (Eastern Time)
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))

    # Convert to UTC and then to milliseconds since epoch
    start_time_utc = start_date.astimezone(pytz.utc)
    end_time_utc = end_date.astimezone(pytz.utc)
    start_time_ms = int(start_time_utc.timestamp() * 1000)
    end_time_ms = int(end_time_utc.timestamp() * 1000)

    # Fetch the historical data
    candles = fetch_dexscreener_data(pair_id, start_time_ms, end_time_ms)

    if candles is None:
        print("recommendation: p4")  # Unable to resolve due to data fetch failure
        return

    # Check if the price dipped to or below the target price
    if check_price_dip_to_target(candles, target_price):
        print("recommendation: p2")  # Yes, price dipped to $0.75 or lower
    else:
        print("recommendation: p1")  # No, price did not dip to $0.75 or lower

if __name__ == "__main__":
    main()