import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_ENDPOINT = "https://api.binance.com/api/v3/klines"
PROXY_API_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def fetch_data_from_binance(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logger.error(f"Failed to fetch data from proxy endpoint: {e}. Trying primary endpoint.")
        # Fallback to the primary endpoint
        try:
            response = requests.get(PRIMARY_API_ENDPOINT, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Failed to fetch data from both endpoints: {e}")
            raise

def convert_to_utc_timestamp(date_str, time_str, timezone_str):
    """
    Converts local time to UTC timestamp.
    """
    local_tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_dt = local_tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    # Specific date and time for the query
    date_str = "2025-06-18"
    time_str = "22:00"
    timezone_str = "US/Eastern"
    symbol = "ETHUSDT"
    interval = "1h"

    # Convert specified time to UTC timestamp
    start_time = convert_to_utc_timestamp(date_str, time_str, timezone_str)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch data from Binance
    try:
        data = fetch_data_from_binance(symbol, interval, start_time, end_time)
        if data and len(data) > 0:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            if close_price >= open_price:
                print("recommendation: p2")  # Up
            else:
                print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # Unknown/50-50 if no data
    except Exception as e:
        print("recommendation: p3")  # Unknown/50-50 on error

if __name__ == "__main__":
    main()