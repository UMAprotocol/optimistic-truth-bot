import requests
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os
import logging

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_binance_data(symbol, interval, start_time):
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
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched from proxy endpoint.")
        return data
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}. Trying primary endpoint.")
        # Fallback to primary endpoint
        response = requests.get(primary_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched from primary endpoint.")
        return data

def resolve_market(data):
    """
    Resolves the market based on the fetched data.
    """
    if not data or len(data) == 0 or len(data[0]) < 5:
        logging.error("Invalid data received.")
        return "p3"  # Unknown/50-50 if data is invalid

    open_price = float(data[0][1])
    close_price = float(data[0][4])
    change_percentage = ((close_price - open_price) / open_price) * 100

    if change_percentage >= 0:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to execute the market resolution.
    """
    # Define the parameters for the query
    symbol = "BTCUSDT"
    interval = "1h"
    event_time = datetime(2025, 6, 11, 20, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    event_time_utc = event_time.astimezone(pytz.utc)
    start_time = int(event_time_utc.timestamp() * 1000)  # Convert to milliseconds

    # Fetch data from Binance
    data = get_binance_data(symbol, interval, start_time)

    # Resolve the market based on the data
    resolution = resolve_market(data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()