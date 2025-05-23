import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
FDV_TARGET = 1_000_000_000  # $1 billion
START_DATE = datetime(2025, 4, 1, 15, 0)  # April 1, 2025, 3:00 PM ET
END_DATE = datetime(2025, 6, 30, 23, 59)  # June 30, 2025, 11:59 PM ET
DEXSCREENER_URL = "https://dexscreener.com/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"

def fetch_fartcoin_data():
    try:
        # Fetch the data from DexScreener
        response = requests.get(DEXSCREENER_URL)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Failed to fetch data: {e}")
        return None

def check_fdv_threshold(data):
    # Assuming data structure contains a list of 1-minute candle data
    consecutive_count = 0
    for candle in data:
        low_price = candle['low']
        total_supply = candle['totalSupply']  # Assuming total supply is part of each candle data
        fdv = low_price * total_supply
        if fdv >= FDV_TARGET:
            consecutive_count += 1
            if consecutive_count == 5:
                return True
        else:
            consecutive_count = 0
    return False

def main():
    current_time = datetime.now()
    if current_time < START_DATE or current_time > END_DATE:
        print("recommendation: p4")  # Outside the specified time range
        return

    data = fetch_fartcoin_data()
    if not data:
        print("recommendation: p4")  # Data fetch failed or no data available
        return

    if check_fdv_threshold(data):
        print("recommendation: p2")  # FDV reached $1 billion for 5 consecutive minutes
    else:
        print("recommendation: p1")  # FDV did not reach $1 billion for 5 consecutive minutes

if __name__ == "__main__":
    main()