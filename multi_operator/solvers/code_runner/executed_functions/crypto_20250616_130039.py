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
        # First try the proxy endpoint
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

def analyze_price_change(data):
    """
    Analyzes the price change from the fetched data.
    """
    if not data or len(data) < 1 or len(data[0]) < 5:
        logger.error("Invalid data format received.")
        return "p4"  # Unable to determine due to data issues

    open_price = float(data[0][1])
    close_price = float(data[0][4])
    change = (close_price - open_price) / open_price

    if change >= 0:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to handle the resolution of the Ethereum price change.
    """
    # Define the parameters for the query
    symbol = "ETHUSDT"
    interval = "1h"
    # Convert the specific time to UTC timestamp
    target_time = datetime(2025, 6, 16, 8, 0, tzinfo=pytz.timezone("US/Eastern"))
    target_time_utc = target_time.astimezone(pytz.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)

    try:
        data = get_data(symbol, interval, start_time_ms)
        resolution = analyze_price_change(data)
        print(f"recommendation: {resolution}")
    except Exception as e:
        logger.error(f"Error processing the data: {e}")
        print("recommendation: p4")  # Default to unknown if there are errors

if __name__ == "__main__":
    main()