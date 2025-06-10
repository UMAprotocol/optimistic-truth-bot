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
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logger.error(f"Failed to fetch data from proxy: {e}. Trying primary endpoint.")
        try:
            # Fallback to the primary endpoint if proxy fails
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Failed to fetch data from primary endpoint: {e}")
            raise

def get_candle_data(symbol, date_str, hour):
    """
    Retrieves the closing price of a specific hourly candle for the given symbol on Binance.
    """
    tz = pytz.timezone("America/New_York")
    naive_dt = datetime.strptime(date_str, "%Y-%m-%d")
    local_dt = tz.localize(naive_dt.replace(hour=hour))
    utc_dt = local_dt.astimezone(pytz.utc)

    start_time = int(utc_dt.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour in milliseconds

    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        close_price = float(data[0][4])
        open_price = float(data[0][1])
        return close_price, open_price
    else:
        logger.error("No data available for the specified time.")
        return None, None

def resolve_market(symbol, date_str, hour):
    """
    Resolves the market based on the price movement of the specified candle.
    """
    close_price, open_price = get_candle_data(symbol, date_str, hour)
    if close_price is not None and open_price is not None:
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    """
    Main function to resolve the market for Bitcoin on May 28, 2025, 11AM ET candle.
    """
    try:
        result = resolve_market("BTCUSDT", "2025-05-28", 11)
        print(result)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()