import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants for the API endpoints
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

def fetch_price_from_dexscreener():
    """
    Fetches the lowest price of Fartcoin/SOL from Dexscreener within the specified date range.
    Returns the lowest price found or None if no data is available.
    """
    # Define the time range for the query
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    start_timestamp = int(start_date.timestamp() * 1000)  # Convert to milliseconds
    end_timestamp = int(end_date.timestamp() * 1000)  # Convert to milliseconds

    # Construct the URL for the API request
    url = f"https://dexscreener.com/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
    params = {
        "interval": "1m",
        "startTime": start_timestamp,
        "endTime": end_timestamp
    }

    try:
        # Attempt to fetch data from the proxy endpoint
        response = requests.get(PROXY_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as ex:
            print(f"Both endpoints failed: {str(ex)}")
            return None

    # Parse the response to find the lowest price
    lowest_price = None
    for candle in data:
        low_price = float(candle[3])  # "L" price is at index 3 in each candle
        if lowest_price is None or low_price < lowest_price:
            lowest_price = low_price

    return lowest_price

def main():
    # Fetch the lowest price of Fartcoin/SOL during the specified period
    lowest_price = fetch_price_from_dexscreener()

    # Determine the resolution based on the lowest price
    if lowest_price is not None and lowest_price <= 0.40:
        print("recommendation: p2")  # Yes, the price dipped to $0.40 or lower
    else:
        print("recommendation: p1")  # No, the price did not dip to $0.40 or lower

if __name__ == "__main__":
    main()