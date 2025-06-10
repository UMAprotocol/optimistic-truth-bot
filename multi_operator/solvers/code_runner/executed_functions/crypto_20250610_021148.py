import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Constants for the API endpoints and the trading pair
DEXSCREENER_URL = "https://dexscreener.com/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
TRADING_PAIR = "Fartcoin/SOL"
TARGET_PRICE = 1.80
START_DATE = "2025-05-07 15:00:00"
END_DATE = "2025-05-31 23:59:00"
TIMEZONE = "US/Eastern"

def fetch_data(url, params):
    """
    Fetch data from the given URL with specified parameters.
    """
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return None

def check_price_threshold(start_date_str, end_date_str, timezone_str, target_price):
    """
    Check if the price of Fartcoin reached the target price within the specified date range.
    """
    # Convert timezone
    tz = pytz.timezone(timezone_str)
    start_date = tz.localize(datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S"))
    end_date = tz.localize(datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S"))

    # Convert to timestamps
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())

    # Fetch data
    data = fetch_data(DEXSCREENER_URL, {
        "pair": TRADING_PAIR,
        "startTime": start_timestamp,
        "endTime": end_timestamp,
        "interval": "1m"
    })

    if data:
        # Check if any candle's high price meets or exceeds the target price
        for candle in data['data']:
            if candle['H'] >= target_price:
                return True
    return False

def main():
    """
    Main function to determine if Fartcoin reached the target price.
    """
    if check_price_threshold(START_DATE, END_DATE, TIMEZONE, TARGET_PRICE):
        print("recommendation: p2")  # Yes, it reached the target price
    else:
        print("recommendation: p1")  # No, it did not reach the target price

if __name__ == "__main__":
    main()