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
    start_date = datetime(2025, 4, 1, 0, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_date = datetime(2025, 4, 30, 23, 59, 59, tzinfo=pytz.timezone("US/Eastern"))
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)

    params = {
        "symbol": "BTCUSDT",
        "interval": "1m",
        "startTime": start_timestamp,
        "endTime": end_timestamp,
        "limit": 1000  # Maximum limit per API call
    }

    url = "https://api.binance.com/api/v3/klines"
    dipped_to_80k = False

    while start_timestamp < end_timestamp:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if not data:
            break

        for candle in data:
            low_price = float(candle[3])  # Low price is the fourth element in the list
            if low_price <= 80000:
                dipped_to_80k = True
                break

        # Update start_timestamp to the last candle's close time + 1 minute
        last_candle_close_time = data[-1][6]
        start_timestamp = last_candle_close_time + 60000
        params["startTime"] = start_timestamp

        if dipped_to_80k:
            break

    if dipped_to_80k:
        return "recommendation: p2"  # Yes, it dipped to $80k or lower
    else:
        return "recommendation: p1"  # No, it did not dip to $80k or lower

def main():
    result = check_btc_dip_to_80k()
    print(result)

if __name__ == "__main__":
    main()