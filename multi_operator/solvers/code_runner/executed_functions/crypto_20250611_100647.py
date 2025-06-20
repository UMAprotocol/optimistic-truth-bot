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

def get_binance_price(symbol, start_time):
    """
    Fetches the price change for a cryptocurrency pair on Binance at a specific time.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        start_time: Start time for the 1-hour candle in milliseconds

    Returns:
        Price change percentage as float or None if data cannot be fetched
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
            return ((close_price - open_price) / open_price) * 100
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                open_price = float(data[0][1])
                close_price = float(data[0][4])
                return ((close_price - open_price) / open_price) * 100
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}")
            return None

def main():
    """
    Main function to determine if the price of BTCUSDT went up or down at a specific time.
    """
    # Specific date and time for the query
    date_str = "2025-06-11"
    hour = 5  # 5 AM ET
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"

    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    target_time_local = tz.localize(datetime.strptime(f"{date_str} {hour}:00:00", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)

    # Get the price change percentage
    price_change = get_binance_price(symbol, start_time_ms)

    # Determine the resolution based on the price change
    if price_change is None:
        print("recommendation: p3")  # Unknown or data fetch error
    elif price_change >= 0:
        print("recommendation: p2")  # Price went up
    else:
        print("recommendation: p1")  # Price went down

if __name__ == "__main__":
    main()