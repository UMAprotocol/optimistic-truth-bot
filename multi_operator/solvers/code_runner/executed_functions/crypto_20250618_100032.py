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
        return response.json()
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market():
    """
    Resolves the market based on the BTC/USDT price data from Binance.
    """
    # Define the specific date and time for the market resolution
    target_date = datetime(2025, 6, 18, 5, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    target_date_utc = target_date.astimezone(pytz.utc)
    start_time = int(target_date_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch the data
    data = get_data("BTCUSDT", start_time, end_time)

    # Extract open and close prices
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])

        # Determine the resolution based on the open and close prices
        if close_price >= open_price:
            print("recommendation: p2")  # Market resolves to "Up"
        else:
            print("recommendation: p1")  # Market resolves to "Down"
    else:
        print("recommendation: p3")  # Unknown/50-50 if no data available

if __name__ == "__main__":
    resolve_market()