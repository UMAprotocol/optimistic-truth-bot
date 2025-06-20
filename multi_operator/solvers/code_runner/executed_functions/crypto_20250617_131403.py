import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API URLs
PRIMARY_BINANCE_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary request fails.
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
        response = requests.get(PROXY_BINANCE_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}. Falling back to primary endpoint.")
        # Fallback to the primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_BINANCE_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logging.error(f"Both proxy and primary endpoint failed: {e}")
            raise

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the open and close prices of the specified symbol at the target datetime.
    """
    # Convert datetime to the correct format for the API call
    utc_datetime = target_datetime.astimezone(pytz.utc)
    start_time = int(utc_datetime.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # Fetch data
    data = fetch_binance_data(symbol, "1h", start_time, end_time)

    # Extract open and close prices
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        logging.info(f"Open price: {open_price}, Close price: {close_price}")

        # Determine resolution based on price comparison
        if close_price >= open_price:
            return "p2"  # Market resolves to "Up"
        else:
            return "p1"  # Market resolves to "Down"
    else:
        logging.error("No data available to resolve the market.")
        return "p3"  # Unknown/50-50 if no data available

def main():
    # Example: Solana on June 17, 2025, 8AM ET
    symbol = "SOLUSDT"
    target_datetime = datetime(2025, 6, 17, 8, 0, tzinfo=pytz.timezone("US/Eastern"))

    try:
        resolution = resolve_market(symbol, target_datetime)
        print(f"recommendation: {resolution}")
    except Exception as e:
        logging.error(f"Failed to resolve market: {e}")
        print("recommendation: p3")  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    main()