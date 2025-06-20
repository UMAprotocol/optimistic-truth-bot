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

def get_data(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{primary_url}?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {str(e)}")
            raise

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the open and close prices of the specified symbol at the target datetime.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    try:
        candle = get_data(symbol, start_time, end_time)
        open_price = float(candle[1])
        close_price = float(candle[4])

        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    except Exception as e:
        logger.error(f"Error resolving market: {e}")
        return "p3"  # Unknown/50-50 if there's an error

def main():
    """
    Main function to handle the resolution of the market.
    """
    # Example date and time for the market resolution
    target_datetime = datetime(2025, 6, 19, 10, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "SOLUSDT"

    resolution = resolve_market(symbol, target_datetime)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()