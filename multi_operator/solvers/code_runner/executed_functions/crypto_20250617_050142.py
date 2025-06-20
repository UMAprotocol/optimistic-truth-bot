import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance using the proxy endpoint with a fallback to the primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(f"{PROXY_ENDPOINT}", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}. Falling back to primary endpoint.")
        # Fallback to the primary endpoint
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logging.error(f"Both endpoints failed: {e}")
            raise

def convert_to_utc_timestamp(date_str, hour, minute, timezone_str):
    """
    Converts local time to UTC timestamp.
    """
    tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {hour}:{minute}", "%Y-%m-%d %H:%M")
    local_dt = tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    """
    Main function to determine if the price of BTC/USDT went up or down.
    """
    # Define the date and time for the event
    date_str = "2025-06-17"
    hour = 0  # 12 AM ET
    minute = 0
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"
    interval = "1h"

    # Convert event time to UTC timestamp
    start_time = convert_to_utc_timestamp(date_str, hour, minute, timezone_str)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch price data
    try:
        data = fetch_price_data(symbol, interval, start_time, end_time)
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            if close_price >= open_price:
                print("recommendation: p2")  # Up
            else:
                print("recommendation: p1")  # Down
    except Exception as e:
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()