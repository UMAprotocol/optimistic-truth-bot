import requests
import os
from datetime import datetime, timedelta
from pytz import timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants for the API endpoints
DEXSCREENER_API_URL = "https://api.dexscreener.io/latest/dex/pairs/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"

# Timezone and time range settings
ET_TIMEZONE = timezone('US/Eastern')
START_DATE = datetime(2025, 5, 7, 15, 0, tzinfo=ET_TIMEZONE)
END_DATE = datetime(2025, 5, 31, 23, 59, tzinfo=ET_TIMEZONE)
TARGET_PRICE = 3.00

def fetch_dexscreener_data():
    try:
        response = requests.get(DEXSCREENER_API_URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch data from Dexscreener: {str(e)}")
        return None

def check_price_threshold(data):
    if not data or 'pair' not in data or 'candles' not in data['pair']:
        print("Invalid data format or missing data.")
        return "recommendation: p4"

    candles = data['pair']['candles']
    for candle in candles:
        if 'h' in candle:
            high_price = float(candle['h'])
            if high_price >= TARGET_PRICE:
                return "recommendation: p2"  # Yes, price reached $3.00 or higher
    return "recommendation: p1"  # No, price did not reach $3.00

def main():
    data = fetch_dexscreener_data()
    result = check_price_threshold(data)
    print(result)

if __name__ == "__main__":
    main()