import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz
import logging

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy API.")
        return data[0][4]  # Close price
    except Exception as e:
        logging.warning(f"Proxy API failed: {e}. Trying primary API.")
        try:
            # Fallback to the primary API endpoint
            response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
            return data[0][4]  # Close price
        except Exception as e:
            logging.error(f"Primary API failed: {e}")
            raise

def convert_to_utc_timestamp(date_str, time_str, timezone_str):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    local_tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    local_dt = local_tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    # Define the dates, times, and timezone
    date1 = "2025-06-10"
    date2 = "2025-06-11"
    time_str = "12:00:00"
    timezone_str = "US/Eastern"
    symbol = "SOLUSDT"

    # Convert times to UTC timestamps
    start_time1 = convert_to_utc_timestamp(date1, time_str, timezone_str)
    end_time1 = start_time1 + 60000  # 1 minute later in milliseconds
    start_time2 = convert_to_utc_timestamp(date2, time_str, timezone_str)
    end_time2 = start_time2 + 60000  # 1 minute later in milliseconds

    # Fetch close prices
    try:
        close_price1 = float(fetch_binance_data(symbol, start_time1, end_time1))
        close_price2 = float(fetch_binance_data(symbol, start_time2, end_time2))

        # Determine the resolution based on close prices
        if close_price1 < close_price2:
            print("recommendation: p2")  # Up
        elif close_price1 > close_price2:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        logging.error(f"Failed to fetch or process data: {e}")
        print("recommendation: p4")  # Unknown or error

if __name__ == "__main__":
    main()