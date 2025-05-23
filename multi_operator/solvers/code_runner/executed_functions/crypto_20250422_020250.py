import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
FDV_TARGET = 1_000_000_000
DEXSCREENER_URL = "https://dexscreener.com/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
START_DATE = datetime(2025, 4, 1, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
END_DATE = datetime(2025, 6, 30, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
TOTAL_SUPPLY = 1000000000  # Placeholder for total supply of Fartcoin

def fetch_price_data():
    """
    Fetches the price data from DexScreener for Fartcoin and checks if FDV reached the target.
    """
    try:
        # Calculate the timestamps for the start and end dates
        start_timestamp = int(START_DATE.timestamp())
        end_timestamp = int(END_DATE.timestamp())

        # Fetch the price data
        response = requests.get(f"{DEXSCREENER_URL}?startTime={start_timestamp}&endTime={end_timestamp}")
        response.raise_for_status()
        data = response.json()

        # Check for consecutive 1-minute candles with the required FDV
        consecutive_count = 0
        for candle in data['data']:
            low_price = candle['low']
            fdv = low_price * TOTAL_SUPPLY
            if fdv >= FDV_TARGET:
                consecutive_count += 1
                if consecutive_count == 5:
                    return True
            else:
                consecutive_count = 0

        return False
    except requests.RequestException as e:
        logging.error(f"Failed to fetch or process data: {e}")
        return None

def main():
    """
    Main function to determine if Fartcoin reached the FDV target.
    """
    result = fetch_price_data()
    if result is True:
        print("recommendation: p2")  # Yes, FDV reached
    elif result is False:
        print("recommendation: p1")  # No, FDV not reached
    else:
        print("recommendation: p3")  # Unknown or error

if __name__ == "__main__":
    main()