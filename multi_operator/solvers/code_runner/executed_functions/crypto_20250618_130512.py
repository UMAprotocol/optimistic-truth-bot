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
PRIMARY_API = "https://api.binance.com/api/v3"
PROXY_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

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
        # Try fetching from proxy API first
        response = requests.get(f"{PROXY_API}", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logging.error(f"Proxy API failed: {e}. Trying primary API.")
        try:
            # Fallback to primary API
            response = requests.get(f"{PRIMARY_API}/klines", params=params, timeout=10)
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
    # Convert target time to UTC milliseconds
    target_time_utc = int(target_time.timestamp() * 1000)
    
    # Fetch data for the 1 hour candle starting at the target time
    data = fetch_binance_data(symbol, "1h", target_time_utc, target_time_utc + 3600000)
    
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
        return "p3"  # Unknown

def main():
    """
    Main function to process the market resolution.
    """
    symbol = "BTCUSDT"
    target_time_str = "2025-06-18 08:00:00"
    timezone_str = "US/Eastern"
    
    # Convert target time to datetime object
    target_time = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
    target_time = pytz.timezone(timezone_str).localize(target_time)
    
    # Resolve the market
    resolution = resolve_market(symbol, target_time)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()