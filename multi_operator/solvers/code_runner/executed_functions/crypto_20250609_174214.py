import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API endpoint for Dexscreener
DEXSCREENER_URL = "https://dexscreener.com/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"

def fetch_fartcoin_prices(start_date, end_date):
    """
    Fetches the Fartcoin/SOL prices from Dexscreener between the specified start and end dates.
    Args:
        start_date (datetime): Start date and time in ET timezone.
        end_date (datetime): End date and time in ET timezone.
    Returns:
        list: List of prices during the specified period.
    """
    prices = []
    # Convert dates to timestamps
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)

    # Construct the URL with the appropriate parameters
    url = f"{DEXSCREENER_URL}?startTime={start_timestamp}&endTime={end_timestamp}&interval=1m"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Extract the 'H' prices from the data
        for candle in data['data']:
            prices.append(candle['H'])

    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")

    return prices

def check_price_threshold(prices, threshold=2.0):
    """
    Checks if any price in the list exceeds the given threshold.
    Args:
        prices (list): List of prices.
        threshold (float): Price threshold to check against.
    Returns:
        bool: True if any price exceeds the threshold, False otherwise.
    """
    return any(price >= threshold for price in prices)

def main():
    # Define the time period for checking the prices
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))

    # Fetch the prices from Dexscreener
    prices = fetch_fartcoin_prices(start_date, end_date)

    # Check if any price reached $2.00 or more
    if check_price_threshold(prices):
        print("recommendation: p2")  # Yes, Fartcoin reached $2.00 or more
    else:
        print("recommendation: p1")  # No, Fartcoin did not reach $2.00

if __name__ == "__main__":
    main()