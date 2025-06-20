import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API = "https://api.binance.com/api/v3"
PROXY_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching from proxy first
        response = requests.get(f"{PROXY_API}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logging.warning(f"Proxy failed with error: {e}. Trying primary API.")
        # Fallback to primary API
        response = requests.get(f"{PRIMARY_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from primary API.")
        return data

def get_price_change(data):
    """
    Calculate the percentage change from open to close price.
    """
    if not data or len(data) < 1 or len(data[0]) < 5:
        logging.error("Invalid data format received.")
        return None
    open_price = float(data[0][1])
    close_price = float(data[0][4])
    if open_price == 0:
        return None
    return ((close_price - open_price) / open_price) * 100

def main():
    # Define the specific event time and symbol
    event_time = datetime(2025, 6, 11, 23, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    symbol = "BTCUSDT"
    interval = "1h"
    
    # Convert event time to UTC and milliseconds
    event_time_utc = event_time.astimezone(pytz.utc)
    start_time = int(event_time_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch data
    data = fetch_binance_data(symbol, interval, start_time, end_time)
    
    # Calculate price change
    price_change = get_price_change(data)
    
    # Determine resolution based on price change
    if price_change is None:
        print("recommendation: p3")  # Unknown or data error
    elif price_change >= 0:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

if __name__ == "__main__":
    main()