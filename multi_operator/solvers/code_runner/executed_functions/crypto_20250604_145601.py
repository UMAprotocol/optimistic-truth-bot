import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Constants for the API endpoint and the Fartcoin/SOL pair ID
DEXSCREENER_API_URL = "https://api.dexscreener.io/latest/dex/tokens/"
FARTCOIN_SOL_PAIR_ID = "bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"

def fetch_fartcoin_prices(start_time, end_time):
    """
    Fetches the historical price data for Fartcoin/SOL from Dexscreener.
    
    Args:
        start_time (datetime): Start time for the data fetch.
        end_time (datetime): End time for the data fetch.
    
    Returns:
        list: List of price data dictionaries.
    """
    # Convert datetime to timestamps in milliseconds
    start_timestamp = int(start_time.timestamp() * 1000)
    end_timestamp = int(end_time.timestamp() * 1000)

    # Construct the URL with the pair ID and timestamps
    url = f"{DEXSCREENER_API_URL}{FARTCOIN_SOL_PAIR_ID}/candles?from={start_timestamp}&to={end_timestamp}&resolution=1"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data['candles']
    except requests.RequestException as e:
        print(f"Failed to fetch data from Dexscreener: {e}")
        return None

def check_price_threshold(candles, threshold=3.0):
    """
    Checks if the price of Fartcoin reached or exceeded the threshold in any candle.
    
    Args:
        candles (list): List of candle data from Dexscreener.
        threshold (float): Price threshold to check.
    
    Returns:
        bool: True if the threshold was reached or exceeded, False otherwise.
    """
    for candle in candles:
        if float(candle['h']) >= threshold:
            return True
    return False

def main():
    # Define the time range for the query
    start_time = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_time = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))

    # Fetch the price data
    candles = fetch_fartcoin_prices(start_time, end_time)

    # Check if the price threshold was reached
    if candles and check_price_threshold(candles):
        print("recommendation: p2")  # Yes, Fartcoin reached $3.00
    else:
        print("recommendation: p1")  # No, Fartcoin did not reach $3.00

if __name__ == "__main__":
    main()