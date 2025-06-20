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

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price(symbol, date_str, hour=12, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the closing price of a cryptocurrency from Binance at a specified time.
    """
    # Convert local time to UTC
    tz = pytz.timezone(timezone_str)
    naive_dt = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
    local_dt = tz.localize(naive_dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    timestamp = int(utc_dt.timestamp() * 1000)  # Convert to milliseconds

    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 60000  # 1 minute later
    }

    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        logger.error(f"Proxy failed, error: {e}. Trying primary API.")
        # Fallback to primary API if proxy fails
        response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price

def main():
    symbol = "XRPUSDT"
    date1 = "2025-06-09"
    date2 = "2025-06-10"
    hour = 12
    minute = 0
    timezone_str = "US/Eastern"

    try:
        price1 = fetch_price(symbol, date1, hour, minute, timezone_str)
        price2 = fetch_price(symbol, date2, hour, minute, timezone_str)
        if price1 < price2:
            recommendation = "p2"  # Up
        elif price1 > price2:
            recommendation = "p1"  # Down
        else:
            recommendation = "p3"  # 50-50
    except Exception as e:
        logger.error(f"Error fetching prices: {e}")
        recommendation = "p4"  # Unable to resolve

    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()