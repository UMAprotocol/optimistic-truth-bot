import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

def fetch_hyperliquid_data(start_date, end_date):
    """
    Fetches the low prices for the HYPE/USDC trading pair from the Hyperliquid API
    within the specified date range and checks if the price dipped to $9.000 or lower.

    Args:
        start_date (datetime): Start date of the period to check.
        end_date (datetime): End date of the period to check.

    Returns:
        str: 'p1' if the price never dipped to $9.000 or lower, 'p2' if it did.
    """
    base_url = "https://app.hyperliquid.xyz/trade/HYPE/USDC"
    start_timestamp = int(start_date.timestamp()) * 1000  # Convert to milliseconds
    end_timestamp = int(end_date.timestamp()) * 1000  # Convert to milliseconds
    params = {
        "interval": "1m",
        "startTime": start_timestamp,
        "endTime": end_timestamp
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Check if any 'Low' price in the data is $9.000 or lower
        for candle in data:
            if float(candle['low']) <= 9.000:
                return 'p2'  # Yes, price dipped to $9.000 or lower
        return 'p1'  # No, price never dipped to $9.000 or lower

    except requests.RequestException as e:
        print(f"Failed to fetch data from Hyperliquid: {e}")
        return 'p3'  # Unknown/50-50 due to data fetch failure

def main():
    # Define the time period to check
    tz = pytz.timezone('US/Eastern')
    start_date = tz.localize(datetime(2025, 5, 7))
    end_date = tz.localize(datetime(2025, 5, 31, 23, 59))

    # Fetch data and determine the resolution
    resolution = fetch_hyperliquid_data(start_date, end_date)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()