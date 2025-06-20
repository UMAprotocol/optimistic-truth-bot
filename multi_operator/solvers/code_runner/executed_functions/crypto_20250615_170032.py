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

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the symbol at the specified target time.
    """
    # Convert target time to UTC milliseconds
    target_time_utc = target_time.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later

    # Fetch data
    data = get_binance_data(symbol, "1h", start_time_ms, end_time_ms)
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        change_percentage = ((close_price - open_price) / open_price) * 100

        # Determine resolution based on price change
        if change_percentage >= 0:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    """
    Main function to process the market resolution.
    """
    # Example date and time for the market
    target_time = datetime(2025, 6, 15, 12, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "BTCUSDT"

    try:
        result = resolve_market(symbol, target_time)
        print(result)
    except Exception as e:
        logger.error(f"Failed to resolve market: {e}")
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()