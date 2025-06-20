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

# API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance using the proxy endpoint with a fallback to the primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to the primary endpoint
        response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from primary endpoint.")
        return data

def get_eth_price_change():
    """
    Determines the price change of ETH/USDT for the specified 1-hour candle on Binance.
    """
    # Define the specific time for the event
    target_time = datetime(2025, 6, 16, 1, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    target_time_utc = target_time.astimezone(pytz.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later

    # Fetch the price data
    data = fetch_price_data("ETHUSDT", "1h", start_time_ms, end_time_ms)

    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change_percentage = ((close_price - open_price) / open_price) * 100

        # Determine the resolution based on the price change
        if price_change_percentage >= 0:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 due to lack of data

def main():
    """
    Main function to execute the logic.
    """
    try:
        resolution = get_eth_price_change()
        print(f"recommendation: {resolution}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Default to unknown/50-50 if there's an error

if __name__ == "__main__":
    main()