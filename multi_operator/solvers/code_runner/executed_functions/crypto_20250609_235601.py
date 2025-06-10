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

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")

        # Fallback to primary endpoint
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}")
            raise

def get_candle_data(symbol, date_str, hour):
    """
    Retrieves the closing price for a specific hour candle on a given date for the specified symbol.
    """
    tz = pytz.timezone("US/Eastern")
    naive_dt = datetime.strptime(date_str + f" {hour}:00:00", "%Y-%m-%d %H:%M:%S")
    local_dt = tz.localize(naive_dt)
    utc_dt = local_dt.astimezone(pytz.utc)

    start_time = int(utc_dt.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour in milliseconds

    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    if data:
        close_price = float(data[0][4])
        open_price = float(data[0][1])
        return close_price, open_price
    else:
        logger.error("No data returned from API.")
        return None, None

def resolve_market():
    """
    Resolves the market based on the price movement of the BTC/USDT pair on Binance.
    """
    symbol = "BTCUSDT"
    date_str = "2025-05-31"
    hour = 17  # 5 PM ET

    try:
        close_price, open_price = get_candle_data(symbol, date_str, hour)
        if close_price is not None and open_price is not None:
            if close_price >= open_price:
                logger.info("Market resolves to Up.")
                return "recommendation: p2"  # Up
            else:
                logger.info("Market resolves to Down.")
                return "recommendation: p1"  # Down
        else:
            logger.info("Data is insufficient to resolve the market.")
            return "recommendation: p3"  # Unknown/50-50
    except Exception as e:
        logger.error(f"Failed to resolve market due to an error: {e}")
        return "recommendation: p3"  # Unknown/50-50

if __name__ == "__main__":
    result = resolve_market()
    print(result)