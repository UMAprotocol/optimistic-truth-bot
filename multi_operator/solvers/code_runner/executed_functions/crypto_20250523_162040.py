import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_fartcoin_price():
    """
    Fetches the closing price of Fartcoin on May 23, 2025, at 12:00 PM ET from the Hyperliquid API.
    """
    # Define the date and time for the query
    date_str = "2025-05-23"
    hour = 12  # Noon
    minute = 0
    timezone_str = "US/Eastern"

    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    target_time_local = tz.localize(datetime.strptime(f"{date_str} {hour:02d}:{minute:02d}:00", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(pytz.utc)
    timestamp = int(target_time_utc.timestamp())

    # Hyperliquid API endpoint
    url = "https://app.hyperliquid.xyz/api/v1/candles"
    params = {
        "symbol": "FARTCOIN-USD",
        "interval": "1m",
        "startTime": timestamp * 1000,  # Convert to milliseconds
        "endTime": (timestamp + 60) * 1000  # One minute later
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data and 'candles' in data and data['candles']:
            close_price = data['candles'][0]['close']
            logging.info(f"Fartcoin closing price at {date_str} 12:00 ET: {close_price}")
            return close_price
        else:
            logging.error("No data available for the specified time.")
            return None
    except requests.RequestException as e:
        logging.error(f"Failed to fetch data from Hyperliquid: {str(e)}")
        return None

def main():
    """
    Main function to determine the resolution of the market based on the fetched price.
    """
    close_price = fetch_fartcoin_price()
    threshold_price = 1.4001

    if close_price is None:
        print("recommendation: p3")  # Unknown/50-50 if no data could be fetched
    elif close_price >= threshold_price:
        print("recommendation: p2")  # Yes, if the price is above $1.40
    else:
        print("recommendation: p1")  # No, if the price is below $1.40

if __name__ == "__main__":
    main()