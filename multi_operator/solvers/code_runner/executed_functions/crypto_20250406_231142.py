import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def fetch_xrp_low_prices():
    """
    Fetches the 1-minute candle low prices for XRPUSDT on Binance
    for the entire month of April 2025 in the ET timezone.
    Checks if any of these prices dip to $1.90 or lower.

    Returns:
        A string indicating whether XRP dipped to $1.90 or lower.
    """
    # Define the time period for April 2025 in Eastern Time
    start_date = datetime(2025, 4, 1, 0, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 4, 30, 23, 59, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Convert to UTC since Binance API uses UTC
    start_date_utc = start_date.astimezone(pytz.utc)
    end_date_utc = end_date.astimezone(pytz.utc)

    # Convert datetime to milliseconds since this is what Binance API expects
    start_time_ms = int(start_date_utc.timestamp() * 1000)
    end_time_ms = int(end_date_utc.timestamp() * 1000)

    # Binance API endpoint and parameters for 1-minute candles
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "XRPUSDT",
        "interval": "1m",
        "startTime": start_time_ms,
        "endTime": end_time_ms,
        "limit": 1000  # Maximum limit per API call
    }

    try:
        dipped_to_190 = False
        while start_time_ms < end_time_ms:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Check the 'Low' price in each candle
            for candle in data:
                low_price = float(candle[3])
                if low_price <= 1.90:
                    dipped_to_190 = True
                    break

            if dipped_to_190:
                break

            # Update startTime for the next API call
            last_candle_time = int(data[-1][6])
            params['startTime'] = last_candle_time + 1

        if dipped_to_190:
            return "recommendation: p2"  # Yes, it dipped to $1.90 or lower
        else:
            return "recommendation: p1"  # No, it did not dip to $1.90 or lower
    except Exception as e:
        print(f"An error occurred: {e}")
        return "recommendation: p3"  # Unknown/50-50 due to error

def main():
    result = fetch_xrp_low_prices()
    print(result)

if __name__ == "__main__":
    main()