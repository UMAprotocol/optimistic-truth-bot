import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        # Try fetching data from the proxy endpoint first
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}. Falling back to primary endpoint.")
        try:
            # Fallback to the primary endpoint if proxy fails
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logging.error(f"Both proxy and primary endpoints failed: {e}")
            raise

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the open and close prices of the specified symbol at the target time.
    """
    # Convert target time to UTC timestamp in milliseconds
    target_datetime = datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")
    target_timestamp = int(target_datetime.replace(tzinfo=pytz.UTC).timestamp() * 1000)
    
    # Fetch data for the 1-hour interval containing the target time
    data = fetch_binance_data(symbol, "1h", target_timestamp, target_timestamp + 3600000)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        logging.info(f"Open price: {open_price}, Close price: {close_price}")
        
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        logging.error("No data available for the specified time and symbol.")
        return "p3"  # Unknown/50-50

def main():
    """
    Main function to handle the resolution of the Ethereum market.
    """
    symbol = "ETHUSDT"
    target_time = "2025-06-18 23:00:00"  # June 18, 11 PM ET in UTC
    
    try:
        resolution = resolve_market(symbol, target_time)
        print(f"recommendation: {resolution}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Default to unknown/50-50 in case of errors

if __name__ == "__main__":
    main()