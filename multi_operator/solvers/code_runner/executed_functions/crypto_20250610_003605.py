import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Constants
DEXSCREENER_URL = "https://dexscreener.com/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
START_DATE = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
END_DATE = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
TARGET_PRICE = 0.40

def fetch_dexscreener_data():
    """
    Fetches the historical price data for Fartcoin/SOL from Dexscreener.
    """
    try:
        # Convert datetime to timestamps for URL parameters
        start_timestamp = int(START_DATE.timestamp()) * 1000
        end_timestamp = int(END_DATE.timestamp()) * 1000

        # Construct the URL with the appropriate parameters
        url = f"{DEXSCREENER_URL}?startTime={start_timestamp}&endTime={end_timestamp}&interval=1m"
        
        # Make the request
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Check if any minute candle's low price is less than or equal to the target price
        for candle in data['data']:
            if candle['L'] <= TARGET_PRICE:
                return True
        return False
    except requests.RequestException as e:
        print(f"Error fetching data from Dexscreener: {e}")
        return None

def main():
    """
    Main function to determine if Fartcoin dipped to $0.40 or lower.
    """
    result = fetch_dexscreener_data()
    if result is True:
        print("recommendation: p2")  # Yes, it dipped to $0.40 or lower
    elif result is False:
        print("recommendation: p1")  # No, it did not dip to $0.40 or lower
    else:
        print("recommendation: p3")  # Unknown or data fetch error

if __name__ == "__main__":
    main()