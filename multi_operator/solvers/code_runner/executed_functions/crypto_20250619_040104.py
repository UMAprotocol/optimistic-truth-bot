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

def fetch_eth_price(date_str, hour, minute, timezone_str):
    """
    Fetches the ETH/USDT price data from Binance for a specific hour and minute on a given date.
    """
    # Convert local time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    local_dt = tz.localize(datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S"))
    utc_dt = local_dt.astimezone(pytz.utc)
    start_time = int(utc_dt.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # URLs for Binance API
    primary_url = "https://api.binance.com/api/v3/klines"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

    # Parameters for API request
    params = {
        "symbol": "ETHUSDT",
        "interval": "1h",
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }

    # Try fetching data from proxy first
    try:
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return open_price, close_price
    except Exception as e:
        logger.error(f"Proxy failed, error: {e}. Trying primary endpoint.")
        # Fallback to primary endpoint if proxy fails
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                open_price = float(data[0][1])
                close_price = float(data[0][4])
                return open_price, close_price
        except Exception as e:
            logger.error(f"Primary endpoint also failed, error: {e}")
            raise

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the open and close prices.
    """
    if close_price >= open_price:
        return "p2"  # Market resolves to "Up"
    else:
        return "p1"  # Market resolves to "Down"

def main():
    """
    Main function to execute the process.
    """
    try:
        # Specific date and time for the ETH/USDT price check
        date_str = "2025-06-18"
        hour = 23  # 11 PM
        minute = 0
        timezone_str = "US/Eastern"

        # Fetch prices
        open_price, close_price = fetch_eth_price(date_str, hour, minute, timezone_str)
        logger.info(f"Open price: {open_price}, Close price: {close_price}")

        # Resolve the market
        result = resolve_market(open_price, close_price)
        print(f"recommendation: {result}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Resolve as unknown if there's an error

if __name__ == "__main__":
    main()