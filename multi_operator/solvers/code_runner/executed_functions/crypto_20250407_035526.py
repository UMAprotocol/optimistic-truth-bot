import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def check_xrp_dip_to_target_price(start_date, end_date, target_price):
    """
    Checks if XRP dipped to a target price within a specified date range on Binance.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        target_price: Target low price to check

    Returns:
        Boolean indicating if the price dipped to or below the target price
    """
    # Convert dates to UTC timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))  # Include the end day fully

    start_time_ms = int(start_dt.timestamp() * 1000)
    end_time_ms = int(end_dt.timestamp() * 1000)

    # Binance API parameters
    symbol = "XRPUSDT"
    interval = "1m"
    limit = 1000  # Maximum allowed by Binance

    # API endpoint
    url = "https://api.binance.com/api/v3/klines"

    while start_time_ms < end_time_ms:
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
            "startTime": start_time_ms,
            "endTime": min(start_time_ms + limit * 60 * 1000, end_time_ms)
        }

        response = requests.get(url, params=params)
        response.raise_for_status()  # Will raise an exception for HTTP errors
        data = response.json()

        if not data:
            break

        # Check if any low price in the candles is less than or equal to the target price
        for candle in data:
            low_price = float(candle[3])
            if low_price <= target_price:
                return True

        # Update start_time_ms to the last candle's close time
        last_candle_close_time = data[-1][6]
        start_time_ms = last_candle_close_time + 1

    return False

def main():
    # Define the period and target price based on the question
    start_date = "2025-04-01"
    end_date = "2025-04-30"
    target_price = 1.80

    # Check if XRP dipped to $1.80 or lower
    dipped_to_target = check_xrp_dip_to_target_price(start_date, end_date, target_price)

    # Output result
    if dipped_to_target:
        print("XRP dipped to $1.80 or lower in April 2025.")
        print("recommendation: p2")  # Yes
    else:
        print("XRP did not dip to $1.80 in April 2025.")
        print("recommendation: p1")  # No

if __name__ == "__main__":
    main()