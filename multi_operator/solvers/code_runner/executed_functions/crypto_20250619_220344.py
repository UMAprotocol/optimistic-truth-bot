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

def get_eth_price_data(date_str, hour, minute, timezone_str):
    """
    Fetches the ETH/USDT price data for a specific hour and minute on a given date from Binance.
    """
    # Convert local time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    local_dt = tz.localize(datetime.strptime(date_str, "%Y-%m-%d"))
    local_dt = local_dt.replace(hour=hour, minute=minute)
    utc_dt = local_dt.astimezone(pytz.utc)
    start_time = int(utc_dt.timestamp() * 1000)  # Convert to milliseconds

    # Binance API endpoints
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    # Parameters for API request
    params = {
        "symbol": "ETHUSDT",
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }

    # Try proxy endpoint first
    try:
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return open_price, close_price
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")

    # Fallback to primary endpoint
    try:
        response = requests.get(primary_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return open_price, close_price
    except Exception as e:
        logger.error(f"Primary endpoint also failed: {e}")
        raise

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the open and close prices.
    """
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to fetch ETH price data and resolve the market.
    """
    # Specific date and time for the market resolution
    date_str = "2025-06-19"
    hour = 17  # 5 PM ET
    minute = 0
    timezone_str = "US/Eastern"

    try:
        open_price, close_price = get_eth_price_data(date_str, hour, minute, timezone_str)
        result = resolve_market(open_price, close_price)
        print(f"recommendation: {result}")
    except Exception as e:
        logger.error(f"Failed to resolve market: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()