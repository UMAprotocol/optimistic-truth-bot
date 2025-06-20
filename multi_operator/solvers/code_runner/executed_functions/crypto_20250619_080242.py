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

def get_eth_price_data(date_str, hour, minute, timezone_str):
    """
    Fetches the ETH/USDT price data for a specific hour candle on Binance.
    """
    tz = pytz.timezone(timezone_str)
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    dt = tz.localize(datetime(dt.year, dt.month, dt.day, hour, minute, 0))
    dt_utc = dt.astimezone(pytz.utc)
    start_time = int(dt_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": "ETHUSDT",
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        response = requests.get(f"{proxy_url}", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data retrieved from proxy endpoint.")
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        try:
            response = requests.get(f"{primary_url}", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data retrieved from primary endpoint.")
        except Exception as e:
            logger.error(f"Both endpoints failed: {e}")
            return None

    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        logger.error("No data available for the specified time.")
        return None

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the open and close prices.
    """
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to handle the resolution of the Ethereum price market.
    """
    date_str = "2025-06-19"
    hour = 3
    minute = 0
    timezone_str = "US/Eastern"

    price_data = get_eth_price_data(date_str, hour, minute, timezone_str)
    if price_data:
        open_price, close_price = price_data
        resolution = resolve_market(open_price, close_price)
        print(f"recommendation: {resolution}")
    else:
        print("recommendation: p3")  # Unknown/50-50 if no data could be retrieved

if __name__ == "__main__":
    main()