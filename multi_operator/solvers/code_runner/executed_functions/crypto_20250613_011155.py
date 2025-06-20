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
        start_time: Start time in milliseconds for the 1-hour candle

    Returns:
        The percentage change of the candle
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour in milliseconds
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
    return None

def resolve_market():
    """
    Resolves the market based on the Bitcoin price change at a specific time.
    """
    # Specific date and time for the market
    target_date = "2025-06-12"
    target_hour = 20  # 8 PM ET
    target_minute = 0
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"

    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    target_time_local = tz.localize(datetime.strptime(f"{target_date} {target_hour:02d}:{target_minute:02d}:00", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)

    # Get the percentage change of the Bitcoin price
    percentage_change = get_binance_data(symbol, start_time_ms)

    if percentage_change is None:
        print("recommendation: p3")  # Unknown/50-50 if data fetch fails
    elif percentage_change >= 0:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

if __name__ == "__main__":
    resolve_market()