import requests
import logging
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_binance_data(symbol, interval, start_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    primary_url = "https://api.binance.com/api/v3/klines"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }

    try:
        # Try fetching from proxy first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logger.error(f"Proxy failed with error: {e}. Trying primary endpoint.")
        # Fallback to primary endpoint
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Primary endpoint also failed with error: {e}.")
            raise

def convert_to_utc(year, month, day, hour, minute, tz_string):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    local_tz = pytz.timezone(tz_string)
    local_time = local_tz.localize(datetime(year, month, day, hour, minute, 0))
    utc_time = local_time.astimezone(pytz.utc)
    return int(utc_time.timestamp() * 1000)

def main():
    # Specific date and time for the event
    year, month, day = 2025, 6, 18
    hour, minute = 2, 0  # 2 AM ET
    tz_string = "US/Eastern"

    # Convert event time to UTC timestamp in milliseconds
    start_time = convert_to_utc(year, month, day, hour, minute, tz_string)

    # Fetch data from Binance for BTC/USDT
    try:
        data = fetch_binance_data("BTCUSDT", "1h", start_time)
        open_price = float(data[0][1])
        close_price = float(data[0][4])

        # Determine if the price went up or down
        if close_price >= open_price:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logger.error(f"Failed to fetch or process data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if data fetch fails

if __name__ == "__main__":
    main()