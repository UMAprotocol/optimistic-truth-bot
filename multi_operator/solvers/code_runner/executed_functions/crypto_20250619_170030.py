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
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_eth_price(date_str, hour=12, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the open and close price for the ETH/USDT pair on Binance at a specific time.

    Args:
        date_str: Date in YYYY-MM-DD format.
        hour: Hour in 24-hour format.
        minute: Minute.
        timezone_str: Timezone string.

    Returns:
        Tuple of (open_price, close_price) as floats.
    """
    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    target_time_local = tz.localize(datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(pytz.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)

    # Binance API endpoints
    primary_url = "https://api.binance.com/api/v3/klines"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

    # Parameters for the API call
    params = {
        "symbol": "ETHUSDT",
        "interval": "1h",
        "limit": 1,
        "startTime": start_time_ms,
        "endTime": start_time_ms + 3600000  # 1 hour later
    }

    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(primary_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price

def resolve_market():
    """
    Resolves the market based on the ETH/USDT price movement.
    """
    # The specific date and time for the market resolution
    date_str = "2025-06-19"
    hour = 12  # 12 PM ET

    try:
        open_price, close_price = fetch_eth_price(date_str, hour)
        if close_price >= open_price:
            return "recommendation: p2"  # Market resolves to "Up"
        else:
            return "recommendation: p1"  # Market resolves to "Down"
    except Exception as e:
        logger.error(f"Failed to fetch prices: {e}")
        return "recommendation: p3"  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    result = resolve_market()
    print(result)