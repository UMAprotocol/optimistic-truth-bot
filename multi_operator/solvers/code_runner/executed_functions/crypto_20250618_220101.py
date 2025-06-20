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
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from primary endpoint.")
        return data

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the opening and closing prices of the specified symbol at the target time.
    """
    # Convert target time to UTC timestamp
    tz = pytz.timezone("US/Eastern")
    target_time_utc = tz.localize(target_time).astimezone(pytz.utc)
    start_time = int(target_time_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch data
    data = get_binance_data(symbol, "1h", start_time, end_time)
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        logger.info(f"Open price: {open_price}, Close price: {close_price}")

        # Determine resolution
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        logger.error("No data available to resolve the market.")
        return "p3"  # Unknown

def main():
    """
    Main function to handle the resolution of the Bitcoin Up or Down market.
    """
    target_time = datetime(2025, 6, 18, 17, 0)  # June 18, 2025, 5 PM ET
    symbol = "BTCUSDT"
    resolution = resolve_market(symbol, target_time)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()