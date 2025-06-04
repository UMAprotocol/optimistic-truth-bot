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

def get_price_change(data):
    """
    Calculate the percentage change from open to close price from the fetched data.
    """
    if not data or len(data) < 1 or len(data[0]) < 5:
        logger.error("Invalid data format received.")
        return None

    open_price = float(data[0][1])
    close_price = float(data[0][4])
    if open_price == 0:
        logger.error("Open price is zero, cannot calculate percentage change.")
        return None

    return ((close_price - open_price) / open_price) * 100

def main():
    """
    Main function to determine if the price of BTC/USDT went up or down.
    """
    symbol = "BTCUSDT"
    interval = "1h"
    target_date = datetime(2025, 6, 4, 6, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    start_time = int(target_date.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    try:
        data = fetch_binance_data(symbol, interval, start_time, end_time)
        price_change = get_price_change(data)
        if price_change is None:
            print("recommendation: p3")  # Unknown or unable to calculate
        elif price_change >= 0:
            print("recommendation: p2")  # Price went up
        else:
            print("recommendation: p1")  # Price went down
    except Exception as e:
        logger.error(f"Failed to process data: {e}")
        print("recommendation: p3")  # Unknown or error occurred

if __name__ == "__main__":
    main()