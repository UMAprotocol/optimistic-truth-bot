import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# Constants for the API endpoints
DEXSCREENER_API_URL = "https://api.dexscreener.io/latest/dex/pairs/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"

def fetch_dexscreener_data():
    """
    Fetches the historical price data for Fartcoin/SOL from Dexscreener.
    """
    try:
        response = requests.get(DEXSCREENER_API_URL)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Failed to fetch data from Dexscreener: {str(e)}")
        return None

def check_price_threshold(data, start_time, end_time, price_threshold):
    """
    Checks if the price of Fartcoin reached the threshold within the specified time range.

    Args:
        data: The JSON data from Dexscreener.
        start_time: The start datetime object.
        end_time: The end datetime object.
        price_threshold: The price threshold to check against.

    Returns:
        True if the price reached the threshold, False otherwise.
    """
    if not data or 'pair' not in data or 'chartData' not in data['pair']:
        print("Invalid data format received from Dexscreener.")
        return False

    for candle in data['pair']['chartData']:
        candle_time = datetime.fromtimestamp(candle['time'] / 1000, tz=pytz.UTC)
        if start_time <= candle_time <= end_time:
            if candle['h'] >= price_threshold:
                return True
    return False

def main():
    # Define the time range and price threshold based on the ancillary data
    start_time = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_time = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    price_threshold = 1.80

    # Fetch data from Dexscreener
    data = fetch_dexscreener_data()

    # Check if the price threshold was reached
    if check_price_threshold(data, start_time, end_time, price_threshold):
        print("recommendation: p2")  # Yes, price reached $1.80 or higher
    else:
        print("recommendation: p1")  # No, price did not reach $1.80

if __name__ == "__main__":
    main()