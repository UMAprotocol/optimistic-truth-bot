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
        response = requests.get(
            proxy_url,
            params={"symbol": symbol, "interval": interval, "limit": 1, "startTime": start_time, "endTime": end_time},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")

        # Fallback to primary endpoint
        try:
            response = requests.get(
                primary_url,
                params={"symbol": symbol, "interval": interval, "limit": 1, "startTime": start_time, "endTime": end_time},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}")
            raise

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance for the specified time.
    """
    symbol = "BTCUSDT"
    interval = "1h"
    target_date = datetime(2025, 6, 3, 15, 0, 0, tzinfo=pytz.timezone("US/Eastern"))  # June 3, 2025, 3 PM ET
    start_time = int(target_date.timestamp() * 1000)
    end_time = start_time + 3600000  # Plus one hour

    try:
        data = get_binance_data(symbol, interval, start_time, end_time)
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            change_percentage = ((close_price - open_price) / open_price) * 100

            if change_percentage >= 0:
                recommendation = "p2"  # Up
            else:
                recommendation = "p1"  # Down

            logger.info(f"Market resolved: {recommendation} (Change: {change_percentage:.2f}%)")
            return recommendation
        else:
            logger.error("No data available to resolve the market.")
            return "p4"  # Unknown
    except Exception as e:
        logger.error(f"Error resolving market: {e}")
        return "p4"  # Unknown

if __name__ == "__main__":
    result = resolve_market()
    print(f"recommendation: {result}")