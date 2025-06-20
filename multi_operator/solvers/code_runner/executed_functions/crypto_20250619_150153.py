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

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_data_from_binance(symbol, interval, start_time, end_time):
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
        # Try fetching data from the proxy API first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logging.warning(f"Proxy API failed: {e}. Attempting primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logging.error(f"Both API requests failed: {e}")
            raise

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the opening and closing prices of the specified symbol at the target time.
    """
    # Convert target time to UTC milliseconds
    target_time_utc = int(target_time.timestamp() * 1000)
    
    # Fetch the 1-hour candle data for the target time
    data = fetch_data_from_binance(symbol, "1h", target_time_utc, target_time_utc + 3600000)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        
        if close_price >= open_price:
            return "p2"  # Market resolves to "Up"
        else:
            return "p1"  # Market resolves to "Down"
    else:
        return "p3"  # Unknown/50-50 if no data available

def main():
    # Define the symbol and the specific time for the market resolution
    symbol = "ETHUSDT"
    target_time_str = "2025-06-19 10:00:00"
    timezone_str = "US/Eastern"
    
    # Convert the target time to a datetime object
    tz = pytz.timezone(timezone_str)
    target_time = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
    target_time = tz.localize(target_time)
    
    # Resolve the market
    try:
        resolution = resolve_market(symbol, target_time)
        print(f"recommendation: {resolution}")
    except Exception as e:
        print("recommendation: p4")  # Unable to resolve due to an error

if __name__ == "__main__":
    main()