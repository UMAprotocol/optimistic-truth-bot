import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_eth_high_price(start_time, end_time):
    """
    Fetches the highest price of Ethereum from Binance within a specified time range.
    Args:
        start_time (int): Start time in milliseconds since the epoch.
        end_time (int): End time in milliseconds since the epoch.
    Returns:
        float: The highest price of Ethereum if found, otherwise None.
    """
    params = {
        "symbol": "ETHUSDT",
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching from the proxy API first
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            high_prices = [float(candle[2]) for candle in data]
            return max(high_prices)
    except Exception as e:
        logging.warning(f"Proxy API failed, error: {e}. Trying primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                high_prices = [float(candle[2]) for candle in data]
                return max(high_prices)
        except Exception as e:
            logging.error(f"Primary API also failed, error: {e}")
            return None

def check_eth_price_threshold():
    """
    Checks if the Ethereum price reached $2700 at any point in June 2025.
    Returns:
        str: 'p1' if the price did not reach $2700, 'p2' if it did, 'p3' if unknown.
    """
    # Define the time range for June 2025 in Eastern Time
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 6, 1))
    end_date = tz.localize(datetime(2025, 6, 30, 23, 59))

    # Convert to UTC and then to milliseconds since epoch
    start_time_utc = int(start_date.astimezone(pytz.utc).timestamp() * 1000)
    end_time_utc = int(end_date.astimezone(pytz.utc).timestamp() * 1000)

    # Fetch the highest price in the given time range
    highest_price = fetch_eth_high_price(start_time_utc, end_time_utc)

    # Determine the resolution based on the highest price found
    if highest_price is None:
        return "p3"  # Unknown if no data could be retrieved
    elif highest_price >= 2700:
        return "p2"  # Yes, it reached $2700
    else:
        return "p1"  # No, it did not reach $2700

def main():
    resolution = check_eth_price_threshold()
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()