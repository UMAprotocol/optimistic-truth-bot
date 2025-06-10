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

def get_binance_data(symbol, start_time, end_time, proxy_url, primary_url):
    """
    Fetches data from Binance using a proxy and falls back to the primary endpoint if necessary.
    """
    try:
        # Try the proxy endpoint first
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}/klines?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from primary endpoint.")
        return data

def resolve_market(data):
    """
    Resolves the market based on the fetched data.
    """
    if not data or len(data) < 1:
        logger.error("No data available to resolve the market.")
        return "p3"  # Unknown/50-50 if no data available

    open_price = float(data[0][1])
    close_price = float(data[0][4])
    change_percentage = ((close_price - open_price) / open_price) * 100

    if change_percentage >= 0:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    symbol = "BTCUSDT"
    target_date = datetime(2025, 6, 4, 15, 0, 0, tzinfo=pytz.timezone("US/Eastern"))  # June 4, 2025, 3 PM ET
    start_time = int(target_date.timestamp() * 1000)
    end_time = start_time + 3600000  # Plus one hour

    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3"

    data = get_binance_data(symbol, start_time, end_time, proxy_url, primary_url)
    resolution = resolve_market(data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()