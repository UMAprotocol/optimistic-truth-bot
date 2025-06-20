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

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def get_data(symbol, interval, start_time):
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
        if data:
            return data[0]
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")

    try:
        # Fall back to primary endpoint if proxy fails
        response = requests.get(primary_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        logger.error(f"Primary endpoint also failed: {str(e)}")
        raise

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the symbol at the specified target time.
    """
    try:
        # Convert target time to UTC milliseconds
        target_time_utc = int(target_time.timestamp() * 1000)
        data = get_data(symbol, "1h", target_time_utc)

        if data:
            open_price = float(data[1])
            close_price = float(data[4])
            change_percentage = ((close_price - open_price) / open_price) * 100

            if change_percentage >= 0:
                return "p2"  # Up
            else:
                return "p1"  # Down
    except Exception as e:
        logger.error(f"Error resolving market: {str(e)}")
        return "p3"  # Unknown/50-50

def main():
    """
    Main function to handle the resolution of the Ethereum market.
    """
    # Example: June 14, 2025, 1 PM ET
    target_time_str = "2025-06-14 13:00:00"
    tz = pytz.timezone("US/Eastern")
    target_time = tz.localize(datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S"))

    resolution = resolve_market("ETHUSDT", target_time)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()