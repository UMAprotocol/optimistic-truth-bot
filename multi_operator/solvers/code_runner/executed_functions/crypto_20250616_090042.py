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
PRIMARY_API_URL = "https://api.binance.com/api/v3"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        response = requests.get(f"{PROXY_API_URL}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}. Falling back to primary endpoint.")
        # Fallback to the primary endpoint
        try:
            response = requests.get(f"{PRIMARY_API_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logging.error(f"Both endpoints failed: {e}")
            raise

def get_eth_price_change():
    """
    Determines if the ETH price went up or down at the specified time and interval.
    """
    # Define the specific time and interval
    target_time = datetime(2025, 6, 16, 4, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    start_time_utc = int(target_time.astimezone(pytz.utc).timestamp() * 1000)
    end_time_utc = start_time_utc + 3600000  # 1 hour later

    # Fetch the price data
    data = fetch_price_data("ETHUSDT", "1h", start_time_utc, end_time_utc)

    # Calculate the price change
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        change = (close_price - open_price) / open_price * 100

        # Determine the resolution based on the price change
        if change >= 0:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 due to lack of data

def main():
    try:
        resolution = get_eth_price_change()
        print(f"recommendation: {resolution}")
    except Exception as e:
        print("recommendation: p3")  # Default to unknown if there's an error

if __name__ == "__main__":
    main()