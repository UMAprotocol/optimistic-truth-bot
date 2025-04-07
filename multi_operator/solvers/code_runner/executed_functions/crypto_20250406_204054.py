import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def check_doge_price_dip_to_threshold(start_date, end_date, threshold_price=0.15):
    """
    Checks if the price of Dogecoin (DOGEUSDT) on Binance dipped to or below a given threshold
    within a specified date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        threshold_price: Price threshold to check (default: 0.15)

    Returns:
        True if price dipped to or below the threshold, False otherwise
    """
    # Convert dates to timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))

    start_time_ms = int(start_dt.timestamp() * 1000)
    end_time_ms = int(end_dt.timestamp() * 1000)

    # Binance API endpoint and parameters for 1-minute candles
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "DOGEUSDT",
        "interval": "1m",
        "startTime": start_time_ms,
        "endTime": end_time_ms,
        "limit": 1000  # Maximum limit
    }

    try:
        while True:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                break

            # Check if any candle's low price is below the threshold
            for candle in data:
                low_price = float(candle[3])
                if low_price <= threshold_price:
                    return True

            # Update startTime for next batch of data
            last_candle_time = int(data[-1][6])
            params['startTime'] = last_candle_time + 1

    except requests.RequestException as e:
        print(f"Error fetching data from Binance: {e}")
        return False

    return False

def main():
    # Define the date range for April 2025
    start_date = "2025-04-01"
    end_date = "2025-04-30"
    threshold_price = 0.15

    # Check if Dogecoin dipped to or below $0.15
    result = check_doge_price_dip_to_threshold(start_date, end_date, threshold_price)

    # Print the result with the appropriate recommendation
    if result:
        print("recommendation: p2")  # Yes, it dipped to $0.15 or lower
    else:
        print("recommendation: p1")  # No, it did not dip to $0.15 or lower

if __name__ == "__main__":
    main()