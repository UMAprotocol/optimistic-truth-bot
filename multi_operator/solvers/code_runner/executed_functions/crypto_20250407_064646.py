import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def check_btc_dip_to_75k():
    """
    Checks if Bitcoin price on Binance dipped to $75,000 or lower in April 2025.
    Uses the Binance API to fetch historical 1-minute candle data for the BTCUSDT pair.
    """
    # Define the time period for the query
    start_date = datetime(2025, 4, 1, 0, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_date = datetime(2025, 4, 30, 23, 59, 59, tzinfo=pytz.timezone("US/Eastern"))
    start_time_ms = int(start_date.timestamp() * 1000)
    end_time_ms = int(end_date.timestamp() * 1000)

    # Binance API endpoint for historical klines
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "BTCUSDT",
        "interval": "1m",
        "startTime": start_time_ms,
        "endTime": end_time_ms,
        "limit": 1000  # Maximum limit per API call
    }

    try:
        while True:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                break

            # Check if any candle's low price is $75,000 or lower
            for candle in data:
                low_price = float(candle[3])
                if low_price <= 75000:
                    return "Yes"

            # Update startTime for the next batch of data
            last_candle_time = int(data[-1][6])
            params["startTime"] = last_candle_time + 1

            if last_candle_time >= end_time_ms:
                break

    except requests.RequestException as e:
        print(f"Error fetching data from Binance: {e}")
        return "Error"

    return "No"

def main():
    result = check_btc_dip_to_75k()
    if result == "Yes":
        print("recommendation: p2")  # Yes, Bitcoin dipped to $75k or lower
    elif result == "No":
        print("recommendation: p1")  # No, Bitcoin did not dip to $75k or lower
    else:
        print("recommendation: p3")  # Unknown or error

if __name__ == "__main__":
    main()