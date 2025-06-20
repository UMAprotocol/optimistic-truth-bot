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
        # Try fetching data from the proxy endpoint first
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logger.error(f"Proxy API failed: {e}, trying primary API.")
        try:
            # Fallback to the primary API endpoint
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
    if not data or len(data) == 0 or len(data[0]) < 5:
        logger.error("Invalid data format received.")
        return "p3"  # Unknown or 50-50 if data is insufficient

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
    # Define the specific time and date for the event
    event_time = datetime(2025, 6, 11, 2, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    start_time = int(event_time.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # Plus one hour

    try:
        data = fetch_binance_data("BTCUSDT", "1h", start_time, end_time)
        result = analyze_price_change(data)
        print(f"recommendation: {result}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown or 50-50 if an error occurs

if __name__ == "__main__":
    main()