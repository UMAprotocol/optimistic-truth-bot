import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Define the API endpoint for Hyperliquid
HYPERLIQUID_ENDPOINT = "https://app.hyperliquid.xyz/trade/HYPE/USDC"

def fetch_hyperliquid_data(start_time, end_time):
    """
    Fetches the 'High' prices of one-minute candles for the HYPE/USDC pair from Hyperliquid
    within the specified timeframe.

    Args:
        start_time (datetime): Start time in UTC.
        end_time (datetime): End time in UTC.

    Returns:
        list of floats: List of high prices.
    """
    # Convert datetime to milliseconds since epoch
    start_time_ms = int(start_time.timestamp() * 1000)
    end_time_ms = int(end_time.timestamp() * 1000)

    # Prepare the request parameters
    params = {
        "symbol": "HYPEUSDC",
        "interval": "1m",
        "startTime": start_time_ms,
        "endTime": end_time_ms
    }

    # Make the request to the Hyperliquid API
    try:
        response = requests.get(HYPERLIQUID_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract the 'High' prices from the data
        high_prices = [float(candle['high']) for candle in data]
        return high_prices

    except requests.RequestException as e:
        print(f"Failed to fetch data from Hyperliquid: {e}")
        return []

def check_price_threshold(prices, threshold=35.0):
    """
    Checks if any of the prices in the list exceed the specified threshold.

    Args:
        prices (list of float): List of prices.
        threshold (float): Price threshold.

    Returns:
        bool: True if any price exceeds the threshold, False otherwise.
    """
    return any(price >= threshold for price in prices)

def main():
    # Define the time range for the query
    start_time = datetime(2025, 5, 7, 16, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_time = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))

    # Convert time to UTC
    start_time_utc = start_time.astimezone(pytz.utc)
    end_time_utc = end_time.astimezone(pytz.utc)

    # Fetch the high prices from Hyperliquid
    high_prices = fetch_hyperliquid_data(start_time_utc, end_time_utc)

    # Check if any price meets or exceeds the threshold
    if check_price_threshold(high_prices):
        print("recommendation: p2")  # Yes, price reached $35 or higher
    else:
        print("recommendation: p1")  # No, price did not reach $35

if __name__ == "__main__":
    main()