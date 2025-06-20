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

def get_binance_data(symbol, interval, start_time, end_time, proxy_first=True):
    """
    Fetches data from Binance API with a fallback mechanism from proxy to primary endpoint.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    urls = [(proxy_url, {'symbol': symbol, 'interval': interval, 'limit': 1, 'startTime': start_time, 'endTime': end_time}),
            (primary_url, {'symbol': symbol, 'interval': interval, 'limit': 1, 'startTime': start_time, 'endTime': end_time})]

    if not proxy_first:
        urls.reverse()

    for url, params in urls:
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][1]), float(data[0][4])  # Open and Close prices
        except Exception as e:
            logger.error(f"Failed to fetch data from {url}: {e}")
            continue
    raise Exception("Both primary and proxy endpoints failed.")

def resolve_market():
    """
    Resolves the market based on the BTC/USDT price data from Binance.
    """
    # Define the specific time and date for the market resolution
    target_date = datetime(2025, 6, 19, 12, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    target_timestamp = int(target_date.timestamp() * 1000)  # Convert to milliseconds

    try:
        open_price, close_price = get_binance_data('BTCUSDT', '1h', target_timestamp, target_timestamp + 3600000)
        logger.info(f"Open price: {open_price}, Close price: {close_price}")

        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    except Exception as e:
        logger.error(f"Error resolving market: {e}")
        return "recommendation: p3"  # Unknown/50-50 due to error

if __name__ == "__main__":
    result = resolve_market()
    print(result)