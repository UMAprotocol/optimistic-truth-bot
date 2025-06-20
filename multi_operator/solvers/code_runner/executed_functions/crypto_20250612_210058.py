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

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance using the proxy endpoint with a fallback to the primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logger.error(f"Failed to fetch data from proxy endpoint: {e}. Trying primary endpoint.")
        try:
            # Fallback to the primary endpoint
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Failed to fetch data from both endpoints: {e}")
            raise

def analyze_price_change(data):
    """
    Analyzes the price change from the fetched data.
    """
    if not data or len(data) == 0 or len(data[0]) < 5:
        logger.error("Invalid data format received.")
        return "p3"  # Unknown/50-50 if data is insufficient or incorrect

    open_price = float(data[0][1])
    close_price = float(data[0][4])
    price_change = close_price - open_price

    if price_change >= 0:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to determine if the price of ETH/USDT went up or down at a specific time.
    """
    symbol = "ETHUSDT"
    interval = "1h"
    # Convert specific time to UTC timestamp
    target_time = datetime(2025, 6, 12, 16, 0, tzinfo=pytz.timezone("US/Eastern"))
    target_time_utc = target_time.astimezone(pytz.utc)
    start_time = int(target_time_utc.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    try:
        data = fetch_price_data(symbol, interval, start_time, end_time)
        resolution = analyze_price_change(data)
        print(f"recommendation: {resolution}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 if an error occurs

if __name__ == "__main__":
    main()