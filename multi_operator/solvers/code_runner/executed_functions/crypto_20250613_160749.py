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
        logger.error(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    raise Exception("Failed to retrieve data from both endpoints.")

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
    date1 = "2025-06-12"
    date2 = "2025-06-13"
    hour = 12  # Noon
    timezone_str = "US/Eastern"

    start_time1 = convert_to_utc_timestamp(date1, hour, 0, timezone_str)
    end_time1 = start_time1 + 60000  # 1 minute later in milliseconds

    start_time2 = convert_to_utc_timestamp(date2, hour, 0, timezone_str)
    end_time2 = start_time2 + 60000  # 1 minute later in milliseconds

    try:
        close_price1 = get_data(symbol, start_time1, end_time1)
        close_price2 = get_data(symbol, start_time2, end_time2)

        if close_price1 < close_price2:
            print("recommendation: p2")  # Up
        elif close_price1 > close_price2:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        logger.error(f"Error in fetching data: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()