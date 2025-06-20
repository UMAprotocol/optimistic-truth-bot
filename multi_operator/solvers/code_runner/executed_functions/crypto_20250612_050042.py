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
        # Try fetching data from the proxy endpoint first
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

def get_eth_price_change():
    """
    Determines if the price of ETH/USDT has gone up or down based on the specified time.
    """
    # Define the time for the 1H candle on June 12, 12 AM ET
    target_time = datetime(2025, 6, 12, 0, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    start_time = int(target_time.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # Fetch the data for the ETH/USDT pair
    try:
        data = fetch_binance_data("ETHUSDT", "1h", start_time, end_time)
        if data and len(data) > 0:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            price_change = close_price - open_price
            recommendation = "p2" if price_change < 0 else "p1"
            logger.info(f"ETH/USDT price change: {price_change} (Open: {open_price}, Close: {close_price})")
            return recommendation
        else:
            logger.error("No data available for the specified time.")
            return "p3"
    except Exception as e:
        logger.error(f"Error fetching or processing data: {e}")
        return "p3"

def main():
    """
    Main function to determine if the price of ETH/USDT went up or down.
    """
    result = get_eth_price_change()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()