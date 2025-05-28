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

def fetch_price(symbol, date_str, timezone_str="US/Eastern"):
    """
    Fetches the closing price of a cryptocurrency from Binance at a specified date and time.
    """
    # Convert date string to UTC timestamp
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    timestamp = int(utc_datetime.timestamp() * 1000)  # Convert to milliseconds

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
        logger.error(f"Proxy failed, error: {e}, trying primary endpoint")
        # Fallback to the primary endpoint if proxy fails
        response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price

def main():
    """
    Main function to determine if the price of XRP/USDT went up or down between two specific times.
    """
    symbol = "XRPUSDT"
    date1 = "2025-05-26 12:00"
    date2 = "2025-05-27 12:00"
    timezone_str = "US/Eastern"

    try:
        price1 = fetch_price(symbol, date1, timezone_str)
        price2 = fetch_price(symbol, date2, timezone_str)
        logger.info(f"Price on {date1}: {price1}")
        logger.info(f"Price on {date2}: {price2}")

        if price1 < price2:
            print("recommendation: p2")  # Up
        elif price1 > price2:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        logger.error(f"Error fetching prices: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()