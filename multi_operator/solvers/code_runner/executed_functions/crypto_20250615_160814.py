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

def fetch_binance_data(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logger.error(f"Proxy failed, error: {e}. Trying primary endpoint.")
        try:
            # Fallback to the primary endpoint if proxy fails
            response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Primary endpoint also failed, error: {e}.")
            raise

def get_close_price(symbol, date_str, timezone_str="US/Eastern"):
    """
    Get the close price for a specific minute candle on Binance.
    """
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    start_time = int(utc_datetime.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later in milliseconds

    data = fetch_binance_data(symbol, start_time, end_time)
    close_price = float(data[0][4])  # Close price is the 5th element in the list
    return close_price

def resolve_market():
    """
    Resolve the market based on the close prices of XRP/USDT on Binance at specific times.
    """
    symbol = "XRPUSDT"
    date1 = "2025-06-14 12:00"
    date2 = "2025-06-15 12:00"
    try:
        close_price1 = get_close_price(symbol, date1)
        close_price2 = get_close_price(symbol, date2)
        if close_price1 < close_price2:
            result = "p2"  # Up
        elif close_price1 > close_price2:
            result = "p1"  # Down
        else:
            result = "p3"  # 50-50
        logger.info(f"Market resolved: {result}")
        print(f"recommendation: {result}")
    except Exception as e:
        logger.error(f"Failed to resolve market: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    resolve_market()