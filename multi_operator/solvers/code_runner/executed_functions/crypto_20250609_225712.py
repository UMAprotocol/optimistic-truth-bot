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

def get_binance_data(symbol, start_time):
    """
    Fetches the 1-hour candle data for a cryptocurrency pair on Binance at a specific start time.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        start_time: Start time for the 1-hour candle in milliseconds

    Returns:
        The percentage change of the candle if data is available, otherwise None.
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
        logger.info("Data fetched successfully from proxy.")
    except Exception as e:
        logger.error(f"Proxy failed with error: {e}. Trying primary endpoint.")
        # Fallback to primary endpoint
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
        except Exception as e:
            logger.error(f"Both endpoints failed: {e}")
            return None

    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        percentage_change = ((close_price - open_price) / open_price) * 100
        return percentage_change
    else:
        return None

def resolve_market():
    """
    Resolves the market based on the BTC/USDT price change for the 1-hour candle starting at 9 AM ET on May 30, 2025.
    """
    # Convert May 30, 2025 9 AM ET to UTC timestamp
    tz = pytz.timezone("US/Eastern")
    dt = datetime(2025, 5, 30, 9, 0, 0, tzinfo=tz)
    dt_utc = dt.astimezone(pytz.utc)
    start_time_ms = int(dt_utc.timestamp() * 1000)

    # Get the percentage change for the BTC/USDT pair
    percentage_change = get_binance_data("BTCUSDT", start_time_ms)

    if percentage_change is None:
        logger.error("Failed to fetch data.")
        return "recommendation: p4"  # Unable to resolve
    elif percentage_change >= 0:
        return "recommendation: p2"  # Market resolves to "Up"
    else:
        return "recommendation: p1"  # Market resolves to "Down"

if __name__ == "__main__":
    result = resolve_market()
    print(result)