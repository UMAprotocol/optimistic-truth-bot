import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def check_ethereum_dip(start_date, end_date, target_price):
    """
    Checks if Ethereum's price dipped to or below the target price on Binance within the specified date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        target_price: Target dip price as float

    Returns:
        Boolean indicating if the dip occurred
    """
    # Convert dates to UTC timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))  # Include the end day fully

    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)

    # Binance API endpoint and parameters for ETHUSDT
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "ETHUSDT",
        "interval": "1m",
        "startTime": start_ts,
        "endTime": end_ts,
        "limit": 1000  # Maximum limit
    }

    try:
        while True:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                break

            # Check if any low price in the candles is below the target price
            for candle in data:
                low_price = float(candle[3])
                if low_price <= target_price:
                    return True

            # Update startTime for next batch of data
            last_candle_time = int(data[-1][6])
            params['startTime'] = last_candle_time + 1

    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

    return False

def main():
    # Define the period and target price based on the question
    start_date = "2025-04-01"
    end_date = "2025-04-30"
    target_price = 1600.0

    # Check for the price dip
    dip_occurred = check_ethereum_dip(start_date, end_date, target_price)

    # Output the result
    if dip_occurred is None:
        print("recommendation: p3")  # Unknown due to error
    elif dip_occurred:
        print("recommendation: p2")  # Yes, dip occurred
    else:
        print("recommendation: p1")  # No, dip did not occur

if __name__ == "__main__":
    main()