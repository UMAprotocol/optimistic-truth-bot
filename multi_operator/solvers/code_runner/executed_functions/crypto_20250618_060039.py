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
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later in milliseconds
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
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched from primary endpoint.")
            return data
        except Exception as e:
            logging.error(f"Primary endpoint also failed: {e}")
            raise

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the open and close prices of the specified symbol at the target datetime.
    """
    # Convert datetime to UTC timestamp in milliseconds
    utc_datetime = target_datetime.astimezone(timezone.utc)
    start_time = int(utc_datetime.timestamp() * 1000)

    # Fetch data from Binance
    data = get_binance_data(symbol, "1h", start_time)
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        logging.info(f"Open price: {open_price}, Close price: {close_price}")

        # Determine resolution based on open and close prices
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        logging.error("No data available to resolve the market.")
        return "p3"  # Unknown/50-50

def main():
    # Example date and time for the market resolution
    target_datetime = datetime(2025, 6, 18, 1, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "BTCUSDT"

    try:
        resolution = resolve_market(symbol, target_datetime)
        print(f"recommendation: {resolution}")
    except Exception as e:
        logging.error(f"Failed to resolve market: {e}")
        print("recommendation: p3")  # Default to unknown if there's an error

if __name__ == "__main__":
    main()