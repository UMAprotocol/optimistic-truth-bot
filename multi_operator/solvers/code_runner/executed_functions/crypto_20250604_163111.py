import requests
import os
from datetime import datetime, timedelta
from pytz import timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
DEXSCREENER_API_URL = "https://api.dexscreener.io/latest/dex/pairs/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
TARGET_PRICE = 0.75
START_DATE = datetime(2025, 5, 7, 15, 0, tzinfo=timezone('US/Eastern'))
END_DATE = datetime(2025, 5, 31, 23, 59, tzinfo=timezone('US/Eastern'))

def fetch_dexscreener_data():
    try:
        response = requests.get(DEXSCREENER_API_URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch data from Dexscreener: {e}")
        return None

def check_price_dip(data):
    if not data or 'pair' not in data or 'candles' not in data['pair']:
        return "p4"  # Unable to resolve due to data issues

    candles = data['pair']['candles']
    for candle in candles:
        # Convert timestamp to datetime in Eastern Time
        candle_time = datetime.fromtimestamp(candle['timestamp'] / 1000, tz=timezone('US/Eastern'))
        if START_DATE <= candle_time <= END_DATE:
            if candle['l'] <= TARGET_PRICE:
                return "p2"  # Yes, price dipped to $0.75 or lower
    return "p1"  # No, price did not dip to $0.75 or lower

def main():
    data = fetch_dexscreener_data()
    result = check_price_dip(data)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()