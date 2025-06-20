import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_data_from_binance(symbol, interval, start_time, end_time):
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
        # Try fetching from proxy first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logging.warning(f"Proxy failed with error: {e}. Trying primary API.")
        try:
            # Fallback to primary API
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logging.error(f"Primary API failed with error: {e}.")
            raise

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the open and close prices of the specified symbol at the target datetime.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch data
    data = fetch_data_from_binance(symbol, "1h", start_time, end_time)

    # Extract open and close prices
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        logging.info(f"Open price: {open_price}, Close price: {close_price}")

        # Determine resolution
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        logging.error("No data available for the given parameters.")
        return "p3"  # Unknown/50-50

def main():
    # Define the symbol and target datetime
    symbol = "ETHUSDT"
    target_datetime = datetime(2025, 6, 18, 3, 0, 0, tzinfo=pytz.timezone("US/Eastern"))

    # Resolve the market
    resolution = resolve_market(symbol, target_datetime)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()