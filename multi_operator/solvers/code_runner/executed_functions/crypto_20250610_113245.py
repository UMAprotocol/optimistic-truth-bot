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

def get_data(symbol, interval, start_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

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
        logger.info("Data fetched from proxy endpoint.")
        return data
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")

        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}")
            raise

def analyze_data(data):
    """
    Analyzes the data to determine if the price went up or down.
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
    Main function to handle the resolution of the market based on Binance data.
    """
    # Example date and time for the market resolution
    target_datetime = datetime(2025, 6, 10, 1, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    target_timestamp = int(target_datetime.timestamp() * 1000)  # Convert to milliseconds

    try:
        data = get_data("BTCUSDT", "1h", target_timestamp)
        result = analyze_data(data)
        print(f"recommendation: {result}")
    except Exception as e:
        logger.error(f"Failed to resolve market due to: {e}")
        print("recommendation: p3")  # Unknown/50-50 if an error occurs

if __name__ == "__main__":
    main()