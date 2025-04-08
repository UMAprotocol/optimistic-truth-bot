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
    """
    # Define the time period for the query
    start_date = datetime(2025, 4, 1, 0, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_date = datetime(2025, 4, 30, 23, 59, 59, tzinfo=pytz.timezone("US/Eastern"))
    start_time_ms = int(start_date.timestamp() * 1000)
    end_time_ms = int(end_date.timestamp() * 1000)

    # Binance API endpoint and parameters for ETHUSDT 1-minute candles
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "ETHUSDT",
        "interval": "1m",
        "startTime": start_time_ms,
        "endTime": end_time_ms,
        "limit": 1000  # Maximum limit per request
    }

    try:
        # Loop through the entire month, fetching candles in batches
        while start_time_ms < end_time_ms:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Check each candle's low price
            for candle in data:
                low_price = float(candle[3])  # Low price is the fourth element
                if low_price <= 1600.00:
                    return "Yes, Ethereum dipped to $1600 or lower."

            # Update startTime for the next batch of data
            last_candle_time = int(data[-1][6])  # End time of the last candle
            params["startTime"] = last_candle_time + 1

        return "No, Ethereum did not dip to $1600 or lower."
    except Exception as e:
        return f"An error occurred: {str(e)}"

def main():
    result = check_ethereum_dip_to_1600()
    print(result)

if __name__ == "__main__":
    main()