import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_data_from_binance(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary request fails.
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
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logging.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to the primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logging.error(f"Primary endpoint also failed: {e}")
            raise

def convert_to_utc_timestamp(date_str, time_str, timezone_str):
    """
    Converts local time to UTC timestamp.
    """
    local_tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    local_dt = local_tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    # Specific event details
    event_date = "2025-06-11"
    event_time = "20:00:00"
    timezone_str = "US/Eastern"
    symbol = "ETHUSDT"
    interval = "1h"

    # Convert event time to UTC timestamp
    start_time = convert_to_utc_timestamp(event_date, event_time, timezone_str)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    # Fetch data from Binance
    try:
        data = fetch_data_from_binance(symbol, interval, start_time, end_time)
        if data and len(data) > 0:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            change_percentage = ((close_price - open_price) / open_price) * 100

            # Determine the resolution based on the change percentage
            if change_percentage >= 0:
                print("recommendation: p2")  # Up
            else:
                print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # Unknown/50-50 if no data
    except Exception as e:
        logging.error(f"Failed to process data: {e}")
        print("recommendation: p3")  # Unknown/50-50 on error

if __name__ == "__main__":
    main()