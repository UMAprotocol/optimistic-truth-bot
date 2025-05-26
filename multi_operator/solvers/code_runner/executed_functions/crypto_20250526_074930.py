import requests
import logging
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

# API endpoints and keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
BINANCE_API_URL = "https://api.binance.com/api/v3/klines"

def get_binance_data(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try proxy first
        response = requests.get(BINANCE_PROXY_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        logger.error(f"Proxy failed, trying primary API: {e}")
        try:
            # Fallback to primary API
            response = requests.get(BINANCE_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price
        except Exception as e:
            logger.error(f"Both proxy and primary API requests failed: {e}")
            raise

def convert_to_utc_timestamp(date_str, hour, minute, timezone_str):
    """
    Converts local time to UTC timestamp.
    """
    tz = pytz.timezone(timezone_str)
    local_time = tz.localize(datetime.strptime(f"{date_str} {hour:02d}:{minute:02d}", "%Y-%m-%d %H:%M"))
    utc_time = local_time.astimezone(pytz.utc)
    return int(utc_time.timestamp() * 1000)  # Convert to milliseconds

def main():
    """
    Main function to determine if Bitcoin price went up or down between two specific times.
    """
    symbol = "BTCUSDT"
    date1 = "2025-05-25"
    date2 = "2025-05-26"
    hour = 12
    minute = 0
    timezone_str = "US/Eastern"

    try:
        start_time1 = convert_to_utc_timestamp(date1, hour, minute, timezone_str)
        end_time1 = start_time1 + 60000  # 1 minute in milliseconds
        start_time2 = convert_to_utc_timestamp(date2, hour, minute, timezone_str)
        end_time2 = start_time2 + 60000

        close_price1 = get_binance_data(symbol, start_time1, end_time1)
        close_price2 = get_binance_data(symbol, start_time2, end_time2)

        if close_price2 > close_price1:
            print("recommendation: p2")  # Up
        elif close_price2 < close_price1:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        logger.error(f"Failed to resolve market due to: {e}")
        print("recommendation: p4")  # Unknown

if __name__ == "__main__":
    main()