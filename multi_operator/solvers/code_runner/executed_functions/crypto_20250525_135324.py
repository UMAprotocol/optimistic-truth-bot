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

def get_data(symbol, start_time, end_time, proxy_url, primary_url):
    """
    Fetches data from Binance API using a proxy and falls back to the primary API if necessary.
    """
    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}/klines?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from primary endpoint.")
        return data

def convert_to_utc_timestamp(date_str, hour, minute, timezone_str):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {hour}:{minute}", "%Y-%m-%d %H:%M")
    local_dt = tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    # Define the parameters for the API call
    symbol = "ETHUSDT"
    date1 = "2025-05-23"
    date2 = "2025-05-24"
    hour = 12
    minute = 0
    timezone_str = "US/Eastern"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3"

    # Convert times to UTC timestamps
    start_time1 = convert_to_utc_timestamp(date1, hour, minute, timezone_str)
    end_time1 = start_time1 + 60000  # 1 minute later
    start_time2 = convert_to_utc_timestamp(date2, hour, minute, timezone_str)
    end_time2 = start_time2 + 60000  # 1 minute later

    # Fetch data
    data1 = get_data(symbol, start_time1, end_time1, proxy_url, primary_url)
    data2 = get_data(symbol, start_time2, end_time2, proxy_url, primary_url)

    # Extract close prices
    close_price1 = float(data1[0][4])
    close_price2 = float(data2[0][4])

    # Determine the resolution
    if close_price1 < close_price2:
        resolution = "p2"  # Up
    elif close_price1 > close_price2:
        resolution = "p1"  # Down
    else:
        resolution = "p3"  # 50-50

    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()