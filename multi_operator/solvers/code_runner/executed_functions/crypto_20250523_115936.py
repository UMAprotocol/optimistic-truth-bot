import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Define the API endpoint for Hyperliquid
HYPERLIQUID_ENDPOINT = "https://app.hyperliquid.xyz/api/v1/candles"

# Define the timezone for the given dates
ET_TIMEZONE = pytz.timezone("US/Eastern")

def fetch_hyperliquid_data(start_time, end_time):
    """
    Fetches the 'High' prices of one-minute candles for the HYPE/USDC pair from Hyperliquid within a specified timeframe.

    Args:
        start_time (datetime): Start time in UTC.
        end_time (datetime): End time in UTC.

    Returns:
        list: List of high prices or an empty list if no data is available.
    """
    params = {
        "symbol": "HYPE/USDC",
        "resolution": "1",  # 1 minute resolution
        "from": int(start_time.timestamp()),
        "to": int(end_time.timestamp())
    }
    try:
        response = requests.get(HYPERLIQUID_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()
        return [float(candle['high']) for candle in data['candles']]
    except Exception as e:
        print(f"Failed to fetch data from Hyperliquid: {str(e)}")
        return []

def check_price_threshold(prices, threshold=35.0):
    """
    Checks if any price in the list exceeds the given threshold.

    Args:
        prices (list): List of float prices.
        threshold (float): Price threshold to check against.

    Returns:
        bool: True if any price exceeds the threshold, False otherwise.
    """
    return any(price >= threshold for price in prices)

def main():
    # Define the time period for the query
    start_time_et = ET_TIMEZONE.localize(datetime(2025, 5, 7, 16, 0, 0))
    end_time_et = ET_TIMEZONE.localize(datetime(2025, 5, 31, 23, 59, 59))

    # Convert time to UTC
    start_time_utc = start_time_et.astimezone(pytz.utc)
    end_time_utc = end_time_et.astimezone(pytz.utc)

    # Fetch the high prices from Hyperliquid
    high_prices = fetch_hyperliquid_data(start_time_utc, end_time_utc)

    # Check if any price reached the threshold
    if check_price_threshold(high_prices):
        print("recommendation: p2")  # Yes, price reached $35 or higher
    else:
        print("recommendation: p1")  # No, price did not reach $35

if __name__ == "__main__":
    main()