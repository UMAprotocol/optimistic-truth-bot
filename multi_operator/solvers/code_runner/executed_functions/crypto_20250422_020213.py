import requests
import os
from datetime import datetime, timedelta
from pytz import timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
FDV_TARGET = 1_000_000_000
START_DATE = datetime(2025, 4, 1, 15, 0, tzinfo=timezone('US/Eastern'))
END_DATE = datetime(2025, 6, 30, 23, 59, tzinfo=timezone('US/Eastern'))
DEXSCREENER_URL = "https://dexscreener.com/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"

def fetch_fartcoin_data():
    try:
        response = requests.get(DEXSCREENER_URL)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Failed to fetch data from DexScreener: {e}")
        return None

def check_fdv_threshold(data):
    consecutive_count = 0
    for candle in data['data']['pair']['hourly']:
        low_price = float(candle['low'])
        total_supply = float(data['data']['pair']['totalSupply'])
        fdv = low_price * total_supply
        if fdv >= FDV_TARGET:
            consecutive_count += 1
            if consecutive_count == 5:
                return True
        else:
            consecutive_count = 0
    return False

def main():
    current_time = datetime.now(timezone('UTC'))
    if current_time < START_DATE or current_time > END_DATE:
        print("recommendation: p4")  # Outside the specified time range
        return

    data = fetch_fartcoin_data()
    if data is None:
        print("recommendation: p4")  # Unable to fetch data
        return

    if check_fdv_threshold(data):
        print("recommendation: p2")  # FDV reached the target
    else:
        print("recommendation: p1")  # FDV did not reach the target

if __name__ == "__main__":
    main()