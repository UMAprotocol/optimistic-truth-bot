import requests
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os
import logging

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        # Try fetching data using the proxy endpoint
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logging.warning(f"Proxy API failed: {e}. Attempting primary API.")
        try:
            # Fallback to the primary API endpoint
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logging.error(f"Primary API also failed: {e}")
            raise

def get_eth_price_change():
    """
    Determines the price change of ETH/USDT at a specific time and resolves the market based on the change.
    """
    # Define the specific time and date
    target_datetime = datetime(2025, 6, 14, 23, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    target_timestamp = int(target_datetime.timestamp() * 1000)  # Convert to milliseconds

    # Fetch the 1-hour candle starting at the target time
    try:
        data = fetch_binance_data("ETHUSDT", "1h", target_timestamp, target_timestamp + 3600000)
        if data and len(data) > 0:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            price_change_percentage = ((close_price - open_price) / open_price) * 100

            # Resolve the market based on the price change
            if price_change_percentage >= 0:
                return "recommendation: p2"  # Up
            else:
                return "recommendation: p1"  # Down
        else:
            return "recommendation: p3"  # Unknown/50-50 if no data
    except Exception as e:
        logging.error(f"Error fetching or processing data: {e}")
        return "recommendation: p3"  # Unknown/50-50 on error

def main():
    result = get_eth_price_change()
    print(result)

if __name__ == "__main__":
    main()