import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# Constants for the API endpoints
DEXSCREENER_API_URL = "https://api.dexscreener.io/latest/dex/tokens"

def fetch_fartcoin_prices(start_date, end_date):
    """
    Fetches the historical price data for Fartcoin from Dexscreener API.
    Args:
        start_date (datetime): Start date of the period to fetch prices for.
        end_date (datetime): End date of the period to fetch prices for.
    Returns:
        list: List of price data where each item contains the low price.
    """
    prices = []
    try:
        # Convert datetime to timestamps
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())

        # Prepare API request
        params = {
            'start': start_timestamp,
            'end': end_timestamp,
            'pairAddress': 'bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw'
        }
        response = requests.get(DEXSCREENER_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract the low prices from the data
        for candle in data['data']['candles']:
            prices.append(float(candle['l']))
    except Exception as e:
        print(f"Failed to fetch or parse data: {e}")
    return prices

def check_price_dip_to_threshold(prices, threshold=0.80):
    """
    Checks if the price dipped to or below the threshold.
    Args:
        prices (list): List of prices to check.
        threshold (float): The threshold to check against.
    Returns:
        bool: True if any price dips to or below the threshold, False otherwise.
    """
    return any(price <= threshold for price in prices)

def main():
    # Define the period to check prices for
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))

    # Fetch prices
    prices = fetch_fartcoin_prices(start_date, end_date)

    # Check if the price dipped to $0.80 or lower
    if check_price_dip_to_threshold(prices):
        print("recommendation: p2")  # Yes, it dipped to $0.80 or lower
    else:
        print("recommendation: p1")  # No, it did not dip to $0.80 or lower

if __name__ == "__main__":
    main()