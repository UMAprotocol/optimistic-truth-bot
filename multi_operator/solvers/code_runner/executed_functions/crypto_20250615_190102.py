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

def analyze_data(data):
    """
    Analyzes the fetched data to determine if the price went up or down.
    """
    if not data or len(data) < 1 or len(data[0]) < 5:
        logger.error("Invalid data format received.")
        return "p3"  # Unknown/50-50 if data is insufficient

    open_price = float(data[0][1])
    close_price = float(data[0][4])

    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to execute the process.
    """
    # Specific date and time for the event
    event_time = datetime(2025, 6, 15, 14, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    event_time_utc = event_time.astimezone(pytz.utc)
    start_time_ms = int(event_time_utc.timestamp() * 1000)

    # Symbol and interval for the query
    symbol = "BTCUSDT"
    interval = "1h"

    try:
        data = get_data(symbol, interval, start_time_ms)
        result = analyze_data(data)
        print(f"recommendation: {result}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 if an error occurs

if __name__ == "__main__":
    main()