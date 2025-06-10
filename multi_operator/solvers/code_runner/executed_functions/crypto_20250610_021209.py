import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
DEXSCREENER_URL = "https://dexscreener.com/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
TARGET_PRICE = 1.80
START_DATE = "2025-05-07 15:00:00"
END_DATE = "2025-05-31 23:59:00"
TIMEZONE = "US/Eastern"

def fetch_dexscreener_data():
    """
    Fetches the historical price data for Fartcoin/SOL from Dexscreener.
    """
    try:
        # Convert dates to UTC for API compatibility
        start_dt = datetime.strptime(START_DATE, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(END_DATE, "%Y-%m-%d %H:%M:%S")
        tz = pytz.timezone(TIMEZONE)
        start_dt = tz.localize(start_dt).astimezone(pytz.utc)
        end_dt = tz.localize(end_dt).astimezone(pytz.utc)

        # Convert datetime to milliseconds since epoch
        start_ts = int(start_dt.timestamp() * 1000)
        end_ts = int(end_dt.timestamp() * 1000)

        # Construct the API URL
        url = f"{DEXSCREENER_URL}?startTime={start_ts}&endTime={end_ts}&interval=1m"

        # Make the API request
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Check if any price reached the target
        for candle in data['data']:
            if float(candle['H']) >= TARGET_PRICE:
                return True
        return False
    except Exception as e:
        logging.error(f"Error fetching data from Dexscreener: {e}")
        return None

def main():
    result = fetch_dexscreener_data()
    if result is True:
        print("recommendation: p2")  # Yes, price reached $1.80 or higher
    elif result is False:
        print("recommendation: p1")  # No, price did not reach $1.80
    else:
        print("recommendation: p3")  # Unknown or error

if __name__ == "__main__":
    main()