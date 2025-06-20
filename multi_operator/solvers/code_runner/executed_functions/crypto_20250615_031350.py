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

def get_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{primary_url}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {str(e)}")
            raise

def resolve_market():
    """
    Resolves the market based on the change in BTC/USDT price for a specific 1-hour candle.
    """
    # Define the specific time for the market resolution
    target_time = datetime(2025, 6, 14, 22, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    start_time = int(target_time.timestamp() * 1000)
    end_time = int((target_time + timedelta(hours=1)).timestamp() * 1000)

    try:
        # Fetch the data for the specified time
        data = get_data("BTCUSDT", "1h", start_time, end_time)
        open_price = float(data[1])
        close_price = float(data[4])

        # Determine if the price went up or down
        if close_price >= open_price:
            logger.info("Market resolves to Up.")
            print("recommendation: p2")  # p2 corresponds to Up
        else:
            logger.info("Market resolves to Down.")
            print("recommendation: p1")  # p1 corresponds to Down
    except Exception as e:
        logger.error(f"Failed to resolve market: {e}")
        print("recommendation: p3")  # p3 corresponds to unknown/50-50

if __name__ == "__main__":
    resolve_market()