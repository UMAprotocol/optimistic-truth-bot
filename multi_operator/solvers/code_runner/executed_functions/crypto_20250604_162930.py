import requests
import os
from datetime import datetime, timedelta
from pytz import timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
DEXSCREENER_URL = "https://api.dexscreener.io/latest/dex/tokens/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
TARGET_PRICE = 0.75
START_DATE = datetime(2025, 5, 7, 15, 0, tzinfo=timezone('US/Eastern'))
END_DATE = datetime(2025, 5, 31, 23, 59, tzinfo=timezone('US/Eastern'))
CURRENT_TIME = datetime.now(timezone('UTC'))

def fetch_dexscreener_data():
    try:
        response = requests.get(DEXSCREENER_URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch data from Dexscreener: {e}")
        return None

def check_price_dip(data):
    if not data or 'pairs' not in data:
        return "p4"  # Unable to resolve due to data issues

    pairs_data = data['pairs']
    for pair in pairs_data:
        for candle in pair['candles']:
            if 'l' in candle and float(candle['l']) <= TARGET_PRICE:
                return "p2"  # Yes, price dipped to $0.75 or lower

    return "p1"  # No, price did not dip to $0.75 or lower

def main():
    if CURRENT_TIME < START_DATE or CURRENT_TIME > END_DATE:
        print("recommendation: p4")  # Outside the event time window
        return

    data = fetch_dexscreener_data()
    recommendation = check_price_dip(data)
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()