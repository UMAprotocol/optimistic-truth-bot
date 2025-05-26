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

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, start_time, end_time):
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
        # Try proxy endpoint first
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Close price
    except Exception as e:
        logger.error(f"Proxy failed, error: {e}, trying primary endpoint.")
        # Fallback to primary endpoint
        response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Close price

def get_unix_time_ms(year, month, day, hour, minute, tz_name):
    """
    Converts a given date and time to UTC Unix time in milliseconds.
    """
    tz = pytz.timezone(tz_name)
    dt = datetime(year, month, day, hour, minute)
    dt_local = tz.localize(dt)
    dt_utc = dt_local.astimezone(pytz.utc)
    return int(dt_utc.timestamp() * 1000)

def main():
    # Define the dates and times for price comparison
    year = 2025
    month = 5
    day1 = 22
    day2 = 23
    hour = 12
    minute = 0
    tz_name = "US/Eastern"
    symbol = "ETHUSDT"

    # Get Unix time in milliseconds for both dates
    time1 = get_unix_time_ms(year, month, day1, hour, minute, tz_name)
    time2 = get_unix_time_ms(year, month, day2, hour, minute, tz_name)

    # Fetch close prices for both times
    close_price_day1 = fetch_binance_data(symbol, time1, time1 + 60000)
    close_price_day2 = fetch_binance_data(symbol, time2, time2 + 60000)

    # Determine the resolution based on the close prices
    if close_price_day2 > close_price_day1:
        recommendation = "p2"  # Up
    elif close_price_day2 < close_price_day1:
        recommendation = "p1"  # Down
    else:
        recommendation = "p3"  # 50-50

    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()