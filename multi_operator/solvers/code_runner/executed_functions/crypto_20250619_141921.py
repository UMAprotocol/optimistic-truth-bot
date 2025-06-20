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

def get_binance_data(symbol, interval, start_time):
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
        "endTime": start_time + 3600000  # 1 hour later
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

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the open and close prices of the specified symbol at the target time.
    """
    # Convert target time to UTC timestamp
    target_time_utc = int(target_time.replace(tzinfo=timezone.utc).timestamp() * 1000)

    # Fetch data from Binance
    data = get_binance_data(symbol, "1h", target_time_utc)

    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])

        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50

def main():
    """
    Main function to handle the resolution of the market.
    """
    # Example: Solana on June 19, 2025, 9AM ET
    symbol = "SOLUSDT"
    target_time = datetime(2025, 6, 19, 9, 0, tzinfo=pytz.timezone("US/Eastern"))

    try:
        resolution = resolve_market(symbol, target_time)
        print(f"recommendation: {resolution}")
    except Exception as e:
        logger.error(f"Failed to resolve market: {e}")
        print("recommendation: p3")  # Default to unknown if there's an error

if __name__ == "__main__":
    main()