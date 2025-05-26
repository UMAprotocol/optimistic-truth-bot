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

def get_binance_price(symbol, date_str, hour, minute, timezone_str):
    """
    Fetches the closing price of a cryptocurrency from Binance at a specific time.
    """
    tz = pytz.timezone(timezone_str)
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    dt = tz.localize(datetime(dt.year, dt.month, dt.day, hour, minute, 0))
    dt_utc = dt.astimezone(pytz.utc)
    timestamp = int(dt_utc.timestamp() * 1000)  # Convert to milliseconds

    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 60000  # 1 minute later
    }

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        logger.error(f"Proxy failed, error: {e}, trying primary endpoint")
        # Fallback to primary endpoint
        response = requests.get(primary_url, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price

def main():
    """
    Main function to determine if the Bitcoin price went up or down between two specific times.
    """
    symbol = "BTCUSDT"
    date1 = "2025-05-25"
    date2 = "2025-05-26"
    hour = 12
    minute = 0
    timezone_str = "US/Eastern"

    try:
        price1 = get_binance_price(symbol, date1, hour, minute, timezone_str)
        price2 = get_binance_price(symbol, date2, hour, minute, timezone_str)
        if price2 > price1:
            print("recommendation: p2")  # Up
        elif price2 < price1:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        logger.error(f"Error fetching prices: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()