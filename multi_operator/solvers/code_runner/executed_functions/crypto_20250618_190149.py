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

def get_data(symbol, start_time):
    """
    Fetches the open and close price for a cryptocurrency pair on Binance
    at a specific start time for a 1-hour interval.

    Args:
        symbol: Trading pair symbol
        start_time: Start time in milliseconds

    Returns:
        Tuple of (open price, close price)
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return open_price, close_price
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                open_price = float(data[0][1])
                close_price = float(data[0][4])
                return open_price, close_price
        except Exception as e:
            logger.error(f"Both endpoints failed: {str(e)}")
            raise

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the open and close prices.

    Args:
        open_price: Opening price of the interval
        close_price: Closing price of the interval

    Returns:
        Market resolution as a string
    """
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to handle the market resolution for Solana on Binance.
    """
    # Specific date and time for the market
    target_datetime = datetime(2025, 6, 18, 14, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    target_timestamp = int(target_datetime.timestamp() * 1000)  # Convert to milliseconds

    try:
        open_price, close_price = get_data("SOLUSDT", target_timestamp)
        resolution = resolve_market(open_price, close_price)
        print(f"recommendation: {resolution}")
    except Exception as e:
        logger.error(f"Failed to resolve market: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()