import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def check_ethereum_dip_to_1600():
    """
    Checks if Ethereum (ETHUSDT) dipped to $1600 or lower in April 2025 on Binance.
    Uses the 1-minute candle "Low" prices.

    Returns:
        A string indicating whether Ethereum dipped to $1600 or lower.
    """
    # Define the time period for checking the prices
    start_date = datetime(2025, 4, 1, 0, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_date = datetime(2025, 4, 30, 23, 59, 59, tzinfo=pytz.timezone("US/Eastern"))
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
        while True:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                break

            # Check if any 1-minute candle has a low price of $1600 or lower
            for candle in data:
                low_price = float(candle[3])  # Low price is the fourth element
                if low_price <= 1600.00:
                    return "Ethereum dipped to $1600 or lower: YES"

            # Update startTime for the next batch of data
            last_candle_time = int(data[-1][6])  # Closing time of the last candle
            params["startTime"] = last_candle_time + 1

            if last_candle_time >= end_time_ms:
                break

    except requests.RequestException as e:
        return f"Failed to fetch data: {str(e)}"

    return "Ethereum dipped to $1600 or lower: NO"

def main():
    result = check_ethereum_dip_to_1600()
    print(result)

if __name__ == "__main__":
    main()