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

# API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, startTime, endTime, use_proxy=False):
    """
    Fetches data from Binance API with a fallback to a proxy if the primary fails.
    """
    url = PROXY_BINANCE_API if use_proxy else PRIMARY_BINANCE_API
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": startTime,
        "endTime": endTime
    }
    try:
        response = requests.get(f"{url}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data[0][4]  # Close price
    except Exception as e:
        if not use_proxy:
            logger.error(f"Failed to fetch data from primary API, trying proxy. Error: {e}")
            return fetch_binance_data(symbol, interval, startTime, endTime, use_proxy=True)
        else:
            logger.error(f"Failed to fetch data from both primary and proxy APIs. Error: {e}")
            raise

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of the symbol at the specified datetime.
    """
    # Convert datetime to UTC milliseconds
    target_time_utc = int(target_datetime.replace(tzinfo=timezone.utc).timestamp() * 1000)
    # Fetch close price at the specified time
    close_price_start = float(fetch_binance_data(symbol, "1h", target_time_utc, target_time_utc))
    close_price_end = float(fetch_binance_data(symbol, "1h", target_time_utc + 3600000, target_time_utc + 3600000))

    # Determine the resolution based on price change
    if close_price_end >= close_price_start:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

def main():
    # Example usage
    symbol = "BTCUSDT"
    target_datetime = datetime(2025, 6, 14, 20, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    try:
        result = resolve_market(symbol, target_datetime)
        print(result)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    main()