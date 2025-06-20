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

def parse_candle_data(data):
    """
    Parses the candle data to extract the opening and closing prices.
    """
    if not data or len(data) == 0:
        logger.error("No data available to parse.")
        return None
    # Extract the first candle
    candle = data[0]
    open_price = float(candle[1])
    close_price = float(candle[4])
    return open_price, close_price

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the opening and closing prices.
    """
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to handle the market resolution.
    """
    # Define the parameters for the query
    symbol = "BTCUSDT"
    interval = "1h"
    # Convert the target time to UTC timestamp
    tz = pytz.timezone("US/Eastern")
    target_time_local = tz.localize(datetime(2025, 6, 14, 3, 0, 0))
    target_time_utc = target_time_local.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    
    # Fetch the data
    data = get_data(symbol, interval, start_time_ms)
    # Parse the candle data
    prices = parse_candle_data(data)
    if prices:
        open_price, close_price = prices
        # Resolve the market
        resolution = resolve_market(open_price, close_price)
        print(f"recommendation: {resolution}")
    else:
        print("recommendation: p3")  # Unknown/50-50 if no data

if __name__ == "__main__":
    main()