import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def check_solana_dip_to_100():
    """
    Checks if the price of Solana (SOLUSDT) on Binance dipped to $100 or below
    in any 1-minute candle in April 2025, Eastern Time.

    Returns:
        A string indicating whether Solana dipped to $100 or below.
    """
    # Define the time period for the query
    start_date = datetime(2025, 4, 1, 0, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 4, 30, 23, 59, 59, tzinfo=pytz.timezone('US/Eastern'))
    start_time_ms = int(start_date.timestamp() * 1000)
    end_time_ms = int(end_date.timestamp() * 1000)

    # Binance API endpoint and parameters for historical 1-minute candles
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "SOLUSDT",
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

            # Check if any candle's low price is $100 or below
            for candle in data:
                low_price = float(candle[3])
                if low_price <= 100.00:
                    return "Yes, Solana dipped to $100 or below."

            # Update startTime for the next batch of data
            last_candle_time = int(data[-1][6])
            params['startTime'] = last_candle_time + 1

            if last_candle_time >= end_time_ms:
                break

    except requests.RequestException as e:
        return f"Error fetching data: {str(e)}"

    return "No, Solana did not dip to $100."

def main():
    result = check_solana_dip_to_100()
    print(result)
    if result.startswith("Yes"):
        print("recommendation: p2")  # Yes
    else:
        print("recommendation: p1")  # No

if __name__ == "__main__":
    main()