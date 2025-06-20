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

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logging.warning(f"Proxy API failed: {e}. Attempting primary API.")
        try:
            # Fallback to the primary API endpoint
            response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logging.error(f"Primary API failed: {e}.")
            raise

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the open and close prices of the specified candle.
    """
    # Convert target time to milliseconds since epoch
    target_time_ms = int(target_time.timestamp() * 1000)
    
    # Fetch the 1-hour candle data for the specified time
    data = fetch_binance_data(symbol, "1h", target_time_ms, target_time_ms + 3600000)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50

def main():
    """
    Main function to execute the market resolution.
    """
    # Define the symbol and the specific time for the market resolution
    symbol = "BTCUSDT"
    target_time = datetime(2025, 6, 18, 6, 0, tzinfo=pytz.timezone("US/Eastern"))
    
    try:
        result = resolve_market(symbol, target_time)
        print(f"recommendation: {result}")
    except Exception as e:
        logging.error(f"Failed to resolve market: {e}")
        print("recommendation: p3")  # Default to unknown/50-50 if there's an error

if __name__ == "__main__":
    main()