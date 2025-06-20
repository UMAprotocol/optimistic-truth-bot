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

def parse_time_to_utc(year, month, day, hour, minute, timezone_str):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(timezone_str)
    local_time = tz.localize(datetime(year, month, day, hour, minute))
    utc_time = local_time.astimezone(pytz.utc)
    return int(utc_time.timestamp() * 1000)

def main():
    # Specific details for the Ethereum price check
    year, month, day = 2025, 6, 16
    hour, minute = 23, 0  # 11 PM ET
    timezone_str = "US/Eastern"
    symbol = "ETHUSDT"
    interval = "1h"
    
    # Convert event time to UTC timestamp in milliseconds
    start_time = parse_time_to_utc(year, month, day, hour, minute, timezone_str)
    
    # Fetch the data from Binance
    data = get_data(symbol, interval, start_time)
    
    # Extract the close price of the 1-hour candle
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        change_percentage = ((close_price - open_price) / open_price) * 100
        
        # Determine the resolution based on the change percentage
        if change_percentage >= 0:
            recommendation = "p2"  # Up
        else:
            recommendation = "p1"  # Down
    else:
        recommendation = "p3"  # Unknown/50-50 if no data available
    
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()