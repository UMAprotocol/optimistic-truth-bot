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

def get_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params={
            "symbol": symbol,
            "interval": interval,
            "limit": 1,
            "startTime": start_time,
            "endTime": end_time
        }, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logger.error(f"Proxy failed with error: {e}. Trying primary endpoint.")

        # Fallback to primary endpoint
        try:
            response = requests.get(primary_url, params={
                "symbol": symbol,
                "interval": interval,
                "limit": 1,
                "startTime": start_time,
                "endTime": end_time
            }, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Primary endpoint failed with error: {e}.")
            raise

def resolve_market():
    """
    Resolves the market based on the change in BTC/USDT price from Binance.
    """
    # Define the time for the 1 hour candle beginning at 2 AM ET on June 7, 2025
    et_timezone = pytz.timezone("US/Eastern")
    target_time = et_timezone.localize(datetime(2025, 6, 7, 2, 0, 0))
    start_time = int(target_time.timestamp() * 1000)
    end_time = int((target_time + timedelta(hours=1)).timestamp() * 1000)

    # Fetch the data
    try:
        data = get_binance_data("BTCUSDT", "1h", start_time, end_time)
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            change_percentage = ((close_price - open_price) / open_price) * 100

            # Determine resolution based on the change percentage
            if change_percentage >= 0:
                print("recommendation: p2")  # Up
            else:
                print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # Unknown/50-50 if no data
    except Exception as e:
        logger.error(f"Failed to resolve market due to error: {e}")
        print("recommendation: p3")  # Unknown/50-50 on error

if __name__ == "__main__":
    resolve_market()