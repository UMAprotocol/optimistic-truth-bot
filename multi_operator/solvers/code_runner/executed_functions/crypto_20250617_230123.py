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
    Fetches price data from Binance API with a fallback to a proxy server.
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
        logger.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logger.error(f"Proxy API failed: {e}, falling back to primary API.")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logger.error(f"Primary API also failed: {e}")
            raise

def analyze_price_change(data):
    """
    Analyzes the price change from the fetched data.
    """
    if not data or len(data) == 0:
        logger.error("No data available to analyze.")
        return "p4"
    open_price = float(data[0][1])
    close_price = float(data[0][4])
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to execute the logic.
    """
    # Define the parameters for the query
    symbol = "ETHUSDT"
    interval = "1h"
    # Convert the specific time to UTC timestamp
    target_time = datetime(2025, 6, 17, 18, 0, tzinfo=pytz.timezone("US/Eastern"))
    target_time_utc = target_time.astimezone(pytz.utc)
    start_time = int(target_time_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    try:
        data = fetch_price_data(symbol, interval, start_time, end_time)
        result = analyze_price_change(data)
        print(f"recommendation: {result}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p4")

if __name__ == "__main__":
    main()