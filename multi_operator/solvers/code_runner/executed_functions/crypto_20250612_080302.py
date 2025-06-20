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
        logger.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(primary_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from primary endpoint.")
        return data

def parse_time_to_utc(year, month, day, hour, minute, tz_info):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    local_dt = datetime(year, month, day, hour, minute, tzinfo=pytz.timezone(tz_info))
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    """
    Main function to determine if the price of ETH/USDT was up or down at a specific time.
    """
    # Specific date and time for the query
    year, month, day, hour, minute = 2025, 6, 12, 3, 0
    tz_info = "US/Eastern"
    symbol = "ETHUSDT"
    interval = "1h"
    
    # Convert specified time to UTC timestamp in milliseconds
    start_time = parse_time_to_utc(year, month, day, hour, minute, tz_info)
    
    # Fetch the data
    data = get_data(symbol, interval, start_time)
    
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        change = (close_price - open_price) / open_price * 100
        
        # Determine the resolution based on the price change
        if change >= 0:
            recommendation = "p2"  # Up
        else:
            recommendation = "p1"  # Down
    else:
        recommendation = "p3"  # Unknown/50-50 if no data
    
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()