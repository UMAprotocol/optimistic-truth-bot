import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Constants for the API endpoint and the specific trading pair
DEXSCREENER_API_URL = "https://api.dexscreener.io/latest/dex/tokens"
FARTCOIN_PAIR_ID = "bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"

def fetch_fartcoin_prices(start_time, end_time):
    """
    Fetches the historical price data for Fartcoin/SOL from Dexscreener API.
    
    Args:
        start_time (datetime): Start time for the data fetch.
        end_time (datetime): End time for the data fetch.
    
    Returns:
        list: List of prices or an empty list if no data is available.
    """
    params = {
        'pairAddress': FARTCOIN_PAIR_ID,
        'from': int(start_time.timestamp()),
        'to': int(end_time.timestamp()),
        'interval': '1m'
    }
    try:
        response = requests.get(DEXSCREENER_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        prices = [float(candle['l']) for candle in data['data']['pair']['candles']]
        return prices
    except Exception as e:
        print(f"Failed to fetch data: {str(e)}")
        return []

def check_price_dip_to_threshold(prices, threshold=0.85):
    """
    Checks if the price dipped to or below the threshold at any point.
    
    Args:
        prices (list): List of prices.
        threshold (float): Price threshold to check against.
    
    Returns:
        bool: True if price dipped to or below the threshold, False otherwise.
    """
    return any(price <= threshold for price in prices)

def main():
    # Define the time range for the query
    start_time = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_time = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Fetch prices from Dexscreener
    prices = fetch_fartcoin_prices(start_time, end_time)
    
    # Check if the price dipped to $0.85 or lower
    if check_price_dip_to_threshold(prices):
        print("recommendation: p2")  # Yes, it dipped to $0.85 or lower
    else:
        print("recommendation: p1")  # No, it did not dip to $0.85 or lower

if __name__ == "__main__":
    main()