import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def check_doge_price_dip_to_threshold(start_date, end_date, threshold_price=0.13):
    """
    Checks if the price of Dogecoin (DOGEUSDT) on Binance dipped to or below a threshold price
    within a specified date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        threshold_price: Price threshold to check (default: 0.13)

    Returns:
        True if price dipped to or below the threshold, False otherwise
    """
    # Convert dates to timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))  # Include the end day fully

    start_time_ms = int(start_dt.timestamp() * 1000)
    end_time_ms = int(end_dt.timestamp() * 1000)

    # Binance API endpoint and parameters for historical 1-minute candles
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
                low_price = float(candle[3])  # Low price is the fourth element
                if low_price <= threshold_price:
                    return True

            # Prepare for the next batch of data
            last_candle_time = int(data[-1][6])  # End time of the last candle
            params['startTime'] = last_candle_time + 1

    except requests.RequestException as e:
        print(f"Error fetching data from Binance: {e}")
        return False

    return False

def main():
    # Define the date range and threshold price for the query
    start_date = "2025-04-01"
    end_date = "2025-04-30"
    threshold_price = 0.13

    # Check if the price of DOGE dipped to or below the threshold
    price_dipped = check_doge_price_dip_to_threshold(start_date, end_date, threshold_price)

    # Output the result
    if price_dipped:
        print("recommendation: p2")  # Yes, price dipped to $0.13 or lower
    else:
        print("recommendation: p1")  # No, price did not dip to $0.13 or lower

if __name__ == "__main__":
    main()