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
    Fetches the Fartcoin price from the Hyperliquid API for the specified date and time.
    """
    # Define the date and time for the query
    date_str = "2025-05-23"
    hour = 12  # Noon
    minute = 0
    timezone_str = "US/Eastern"
    
    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    time_str = f"{hour:02d}:{minute:02d}:00"
    target_time_local = tz.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(pytz.utc)
    timestamp = int(target_time_utc.timestamp())
    
    # Hyperliquid API URL setup
    url = "https://app.hyperliquid.xyz/api/v1/candles"
    params = {
        "symbol": "FARTCOIN-USD",
        "interval": "1m",
        "startTime": timestamp * 1000,  # API expects milliseconds
        "endTime": (timestamp + 60) * 1000  # 1 minute later
    }
    
    try:
        # Make the API request
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract the closing price from the first candle
        close_price = float(data['data'][0]['close'])
        logging.info(f"Fetched close price: {close_price}")
        return close_price
    except Exception as e:
        logging.error(f"Failed to fetch data: {e}")
        return None

def main():
    """
    Main function to determine the resolution of the market based on the fetched price.
    """
    close_price = fetch_fartcoin_price()
    threshold_price = 1.4001
    
    if close_price is None:
        print("recommendation: p3")  # Unknown/50-50 if data fetch fails
    elif close_price >= threshold_price:
        print("recommendation: p2")  # Yes, if price is above $1.40
    else:
        print("recommendation: p1")  # No, if price is below $1.40

if __name__ == "__main__":
    main()