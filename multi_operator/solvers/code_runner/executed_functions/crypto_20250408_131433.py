import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def check_btc_dip_to_80k():
    """
    Checks if the BTCUSDT price on Binance dipped to $80,000 or lower in April 2025.
    Uses the Binance API to fetch historical 1-minute candle data for the entire month.

    Returns:
        A string indicating whether the price dipped to $80,000 or lower.
    """
    # Define the time period for April 2025 in Eastern Time
    start_date = datetime(2025, 4, 1, 0, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 4, 30, 23, 59, 59, tzinfo=pytz.timezone('US/Eastern'))

    # Convert start and end dates to milliseconds since epoch in UTC
    start_time_ms = int(start_date.astimezone(pytz.utc).timestamp() * 1000)
    end_time_ms = int(end_date.astimezone(pytz.utc).timestamp() * 1000)

    # Binance API endpoint for historical klines
    url = "https://api.binance.com/api/v3/klines"

    # Initialize parameters for the API request
    params = {
        "symbol": "BTCUSDT",
        "interval": "1m",
        "startTime": start_time_ms,
        "endTime": end_time_ms,
        "limit": 1000  # Maximum limit per request
    }

    try:
        # Loop through the entire month, fetching data in chunks
        while params['startTime'] < end_time_ms:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Check each candle to see if the low price is $80,000 or lower
            for candle in data:
                low_price = float(candle[3])
                if low_price <= 80000:
                    return "recommendation: p2"  # Yes, dipped to $80k or lower

            # Update startTime for the next request to continue where the last one left off
            last_candle = data[-1]
            params['startTime'] = int(last_candle[6]) + 1  # endTime of the last candle + 1 millisecond

        # If loop completes without finding a dip to $80,000 or lower
        return "recommendation: p1"  # No, did not dip to $80k or lower

    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return "recommendation: p3"  # Unknown/50-50 due to error

if __name__ == "__main__":
    result = check_btc_dip_to_80k()
    print(result)