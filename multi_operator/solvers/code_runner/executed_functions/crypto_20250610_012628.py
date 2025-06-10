import requests
import os
from datetime import datetime, timedelta
from pytz import timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
DEXSCREENER_API_URL = "https://api.dexscreener.io/latest/dex/tokens/"
HOUSE_SOL_PAIR_ID = "gj5t6kjtw3gww7srmhei1ojckayhyvlwb17gktf96hnh"

def fetch_price_data(pair_id, start_date, end_date):
    """
    Fetches price data for a given token pair from Dexscreener.
    Args:
        pair_id (str): The pair ID for which to fetch the data.
        start_date (datetime): Start date for the data.
        end_date (datetime): End date for the data.
    Returns:
        list: List of price data or None if an error occurs.
    """
    try:
        response = requests.get(f"{DEXSCREENER_API_URL}{pair_id}")
        response.raise_for_status()
        data = response.json()
        prices = []
        for pair in data['pairs']:
            for candle in pair['candles']:
                candle_time = datetime.fromtimestamp(candle['time'] / 1000, tz=timezone('UTC'))
                if start_date <= candle_time <= end_date:
                    prices.append(candle['l'])
        return prices
    except Exception as e:
        print(f"Failed to fetch or parse data: {e}")
        return None

def check_price_dip_to_threshold(prices, threshold):
    """
    Checks if the price dipped to or below a certain threshold.
    Args:
        prices (list): List of prices.
        threshold (float): The threshold to check against.
    Returns:
        bool: True if the price dipped to or below the threshold, False otherwise.
    """
    return any(price <= threshold for price in prices)

def main():
    # Define the time period
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=timezone('US/Eastern'))

    # Fetch price data
    prices = fetch_price_data(HOUSE_SOL_PAIR_ID, start_date, end_date)

    if prices is None:
        print("recommendation: p4")  # Unable to resolve due to data fetch failure
    else:
        # Check if the price dipped to $0.02000 or lower
        if check_price_dip_to_threshold(prices, 0.02000):
            print("recommendation: p2")  # Yes, it dipped
        else:
            print("recommendation: p1")  # No, it did not dip

if __name__ == "__main__":
    main()