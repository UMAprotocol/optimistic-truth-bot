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

def get_data(symbol, interval, start_time):
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
        # Try the proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data retrieved from proxy endpoint.")
        return data
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(primary_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data retrieved from primary endpoint.")
        return data

def convert_to_utc(date_str, hour, timezone_str):
    """
    Converts local time to UTC timestamp.
    """
    tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(date_str + f" {hour}:00:00", "%Y-%m-%d %H:%M:%S")
    local_dt = tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def analyze_price_change(data):
    """
    Analyzes the price change from the data returned by Binance.
    """
    if not data or not data[0]:
        logger.error("No data available to analyze.")
        return "p4"
    
    open_price = float(data[0][1])
    close_price = float(data[0][4])
    
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to handle the resolution of the Ethereum price change.
    """
    date_str = "2025-06-13"
    hour = 2  # 2 AM ET
    timezone_str = "US/Eastern"
    symbol = "ETHUSDT"
    interval = "1h"
    
    try:
        utc_start_time = convert_to_utc(date_str, hour, timezone_str)
        data = get_data(symbol, interval, utc_start_time)
        resolution = analyze_price_change(data)
        print(f"recommendation: {resolution}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p4")

if __name__ == "__main__":
    main()