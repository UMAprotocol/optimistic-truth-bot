import requests
import os
from datetime import datetime, timedelta
from pytz import timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
DEXSCREENER_API_URL = "https://api.dexscreener.io/latest/dex/candles"
PAIR_ID = "gj5t6kjtw3gww7srmhei1ojckayhyvlwb17gktf96hnh"
TARGET_PRICE = 0.02500
START_DATE = "2025-05-07T15:00:00"
END_DATE = "2025-05-31T23:59:00"
ET_TZ = timezone('US/Eastern')
UTC_TZ = timezone('UTC')

def fetch_candles(pair_id, from_timestamp, to_timestamp):
    params = {
        "pairAddress": pair_id,
        "from": from_timestamp,
        "to": to_timestamp,
        "interval": "1m"
    }
    try:
        response = requests.get(DEXSCREENER_API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return None

def check_price_dip_to_target(candles_data, target_price):
    if candles_data and 'candles' in candles_data:
        for candle in candles_data['candles']:
            if float(candle['l']) <= target_price:
                return True
    return False

def convert_to_utc_timestamp(date_str, tz_info):
    local_dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
    local_dt = tz_info.localize(local_dt)
    utc_dt = local_dt.astimezone(UTC_TZ)
    return int(utc_dt.timestamp())

def main():
    start_utc_timestamp = convert_to_utc_timestamp(START_DATE, ET_TZ)
    end_utc_timestamp = convert_to_utc_timestamp(END_DATE, ET_TZ)

    candles_data = fetch_candles(PAIR_ID, start_utc_timestamp, end_utc_timestamp)
    if candles_data is None:
        print("recommendation: p4")  # Unable to resolve due to data fetch failure
        return

    if check_price_dip_to_target(candles_data, TARGET_PRICE):
        print("recommendation: p2")  # Yes, price dipped to $0.02500 or lower
    else:
        print("recommendation: p1")  # No, price did not dip to $0.02500 or lower

if __name__ == "__main__":
    main()