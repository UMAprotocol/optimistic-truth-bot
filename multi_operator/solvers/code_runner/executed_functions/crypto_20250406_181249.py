import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def check_ethereum_dip_to_1700():
    """
    Checks if Ethereum (ETHUSDT) dipped to $1700 or lower in April 2025 on Binance.
    Uses the Binance API to fetch historical 1-minute candle data for the ETHUSDT pair.
    """
    # Define the time period for the query
    start_date = datetime(2025, 4, 1, 0, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 4, 30, 23, 59, 59, tzinfo=pytz.timezone('US/Eastern'))
    start_time_ms = int(start_date.timestamp() * 1000)
    end_time_ms = int(end_date.timestamp() * 1000)

    # Binance API endpoint for historical klines
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "ETHUSDT",
        "interval": "1m",
        "startTime": start_time_ms,
        "endTime": end_time_ms,
        "limit": 1000  # Maximum limit per request
    }

    try:
        dipped_to_1700 = False
        while True:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                break

            # Check if any 'Low' price in the candles is $1700 or lower
            for candle in data:
                low_price = float(candle[3])
                if low_price <= 1700.00:
                    dipped_to_1700 = True
                    break

            if dipped_to_1700:
                break

            # Update startTime for the next batch of data
            last_candle = data[-1]
            last_candle_close_time = int(last_candle[6])
            params['startTime'] = last_candle_close_time + 1

        if dipped_to_1700:
            print("Ethereum dipped to $1700 or lower in April 2025.")
            print("recommendation: p2")  # Yes
        else:
            print("Ethereum did not dip to $1700 in April 2025.")
            print("recommendation: p1")  # No

    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    check_ethereum_dip_to_1700()