import requests
import os
from datetime import datetime, timedelta
from pytz import timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
DEXSCREENER_API_URL = "https://api.dexscreener.io/latest/dex/tokens/"
HOUSE_SOL_PAIR_ID = "gj5t6kjtw3gww7srmhei1ojckayhyvlwb17gktf96hnh"
TARGET_PRICE = 0.30000
START_DATE = datetime(2025, 5, 7, 15, 0, tzinfo=timezone('US/Eastern'))
END_DATE = datetime(2025, 5, 31, 23, 59, tzinfo=timezone('US/Eastern'))

def fetch_data(pair_id):
    try:
        response = requests.get(f"{DEXSCREENER_API_URL}{pair_id}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return None

def check_price_threshold(data, target_price):
    if data:
        pairs = data.get('pairs', [])
        for pair in pairs:
            candles = pair.get('candles', [])
            for candle in candles:
                if float(candle['h']) >= target_price:
                    return True
    return False

def main():
    current_time = datetime.now(timezone('UTC'))
    if current_time < START_DATE or current_time > END_DATE:
        print("recommendation: p4")  # Outside the event time window
        return

    data = fetch_data(HOUSE_SOL_PAIR_ID)
    if data is None:
        print("recommendation: p3")  # Unable to fetch data
        return

    if check_price_threshold(data, TARGET_PRICE):
        print("recommendation: p2")  # Price reached the target
    else:
        print("recommendation: p1")  # Price did not reach the target

if __name__ == "__main__":
    main()