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
        return response.json()
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        return response.json()

def convert_to_utc_timestamp(date_str, hour, minute, timezone_str):
    """
    Converts local time to UTC timestamp.
    """
    tz = pytz.timezone(timezone_str)
    local_time = tz.localize(datetime.strptime(f"{date_str} {hour:02d}:{minute:02d}:00", "%Y-%m-%d %H:%M:%S"))
    utc_time = local_time.astimezone(pytz.utc)
    return int(utc_time.timestamp() * 1000)

def main():
    """
    Main function to fetch and compare Ethereum prices on specified dates.
    """
    symbol = "ETHUSDT"
    timezone_str = "US/Eastern"
    date1_str = "2025-06-18"
    date2_str = "2025-06-19"
    hour = 12
    minute = 0

    start_time1 = convert_to_utc_timestamp(date1_str, hour, minute, timezone_str)
    end_time1 = start_time1 + 60000  # 1 minute in milliseconds

    start_time2 = convert_to_utc_timestamp(date2_str, hour, minute, timezone_str)
    end_time2 = start_time2 + 60000  # 1 minute in milliseconds

    try:
        data1 = get_data(symbol, start_time1, end_time1)
        data2 = get_data(symbol, start_time2, end_time2)

        close_price1 = float(data1[0][4])
        close_price2 = float(data2[0][4])

        if close_price1 < close_price2:
            print("recommendation: p2")  # Up
        elif close_price1 > close_price2:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        logger.error(f"Failed to fetch or process data: {e}")
        print("recommendation: p4")  # Unknown or error

if __name__ == "__main__":
    main()