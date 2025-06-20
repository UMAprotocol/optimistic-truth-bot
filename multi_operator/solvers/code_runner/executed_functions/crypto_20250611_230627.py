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
    Fetches data from Binance API with a fallback to a proxy if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try proxy endpoint first
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logger.error(f"Proxy failed, error: {e}. Trying primary endpoint.")
        try:
            # Fallback to primary endpoint
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Both proxy and primary endpoints failed, error: {e}.")
            raise

def get_eth_price_change():
    """
    Determines if the ETH price went up or down at the specified time.
    """
    # Define the specific time and date for the query
    target_date = datetime(2025, 6, 11, 18, 0, 0, tzinfo=pytz.timezone('US/Eastern'))  # June 11, 6PM ET
    start_time = int(target_date.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # Plus one hour

    # Fetch data for ETHUSDT
    data = fetch_binance_data("ETHUSDT", "1h", start_time, end_time)
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = close_price - open_price
        recommendation = "p2" if price_change < 0 else "p1"
        logger.info(f"ETH price change from {open_price} to {close_price}: {'down' if price_change < 0 else 'up'}")
        return recommendation
    else:
        logger.error("No data available to determine price change.")
        return "p3"  # Unknown or 50-50 if no data available

def main():
    try:
        result = get_eth_price_change()
        print(f"recommendation: {result}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown or 50-50 if error occurs

if __name__ == "__main__":
    main()