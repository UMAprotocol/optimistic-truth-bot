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

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def get_data(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price

def convert_to_utc_timestamp(date_str, hour=12, minute=0, timezone_str="US/Eastern"):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
    local_dt = tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    """
    Main function to determine if Ethereum price went up or down between two specific times.
    """
    symbol = "ETHUSDT"
    date1 = "2025-06-10"
    date2 = "2025-06-11"
    hour = 12  # Noon
    minute = 0
    timezone_str = "US/Eastern"

    start_time1 = convert_to_utc_timestamp(date1, hour, minute, timezone_str)
    start_time2 = convert_to_utc_timestamp(date2, hour, minute, timezone_str)

    try:
        close_price1 = get_data(symbol, start_time1, start_time1 + 60000)
        close_price2 = get_data(symbol, start_time2, start_time2 + 60000)

        if close_price1 is not None and close_price2 is not None:
            if close_price2 > close_price1:
                print("recommendation: p2")  # Up
            elif close_price2 < close_price1:
                print("recommendation: p1")  # Down
            else:
                print("recommendation: p3")  # 50-50
        else:
            print("recommendation: p4")  # Unknown or data fetch error
    except Exception as e:
        logger.error(f"Error during data fetch or processing: {e}")
        print("recommendation: p4")

if __name__ == "__main__":
    main()