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

def get_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params={
            "symbol": symbol,
            "interval": interval,
            "limit": 1,
            "startTime": start_time,
            "endTime": end_time
        }, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}, falling back to primary endpoint")

    try:
        # Fallback to primary endpoint
        response = requests.get(primary_url, params={
            "symbol": symbol,
            "interval": interval,
            "limit": 1,
            "startTime": start_time,
            "endTime": end_time
        }, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        logging.error(f"Both endpoints failed: {e}")
        raise

def resolve_market():
    """
    Resolves the market based on the BTC/USDT price data from Binance.
    """
    # Define the specific time and date for the market
    target_datetime = datetime(2025, 6, 18, 7, 0, tzinfo=pytz.timezone('US/Eastern'))
    target_timestamp = int(target_datetime.timestamp() * 1000)  # Convert to milliseconds

    # Fetch the data for the 1-hour interval containing the target time
    data = get_binance_data("BTCUSDT", "1h", target_timestamp, target_timestamp + 3600000)

    if data:
        open_price = float(data[1])
        close_price = float(data[4])

        # Determine the market resolution based on the open and close prices
        if close_price >= open_price:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 if no data is available

if __name__ == "__main__":
    resolve_market()