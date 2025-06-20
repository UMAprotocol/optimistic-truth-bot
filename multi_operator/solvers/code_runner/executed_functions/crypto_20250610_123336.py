import requests
import logging
from datetime import datetime
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

def get_binance_price(symbol, date_str, hour=12, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the closing price of a cryptocurrency from Binance at a specified date and time.
    """
    # Convert local time to UTC
    tz = pytz.timezone(timezone_str)
    naive_dt = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
    local_dt = tz.localize(naive_dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    timestamp = int(utc_dt.timestamp() * 1000)  # Convert to milliseconds

    # URLs for Binance API
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    # Parameters for API request
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 60000  # 1 minute later
    }

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        logger.error(f"Proxy failed, trying primary endpoint: {e}")
        # Fallback to primary endpoint
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            close_price = float(data[0][4])
            return close_price
        except Exception as e:
            logger.error(f"Both proxy and primary endpoints failed: {e}")
            raise

def resolve_market():
    """
    Resolves the market based on the closing prices of XRP/USDT on Binance.
    """
    symbol = "XRPUSDT"
    date1 = "2025-06-08"
    date2 = "2025-06-09"
    hour = 12
    minute = 0
    timezone_str = "US/Eastern"

    try:
        price1 = get_binance_price(symbol, date1, hour, minute, timezone_str)
        price2 = get_binance_price(symbol, date2, hour, minute, timezone_str)
        if price1 < price2:
            result = "p2"  # Up
        elif price1 > price2:
            result = "p1"  # Down
        else:
            result = "p3"  # 50-50
        print(f"recommendation: {result}")
    except Exception as e:
        logger.error(f"Failed to resolve market: {e}")
        print("recommendation: p4")

if __name__ == "__main__":
    resolve_market()