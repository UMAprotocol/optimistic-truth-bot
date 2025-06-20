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

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance using the proxy and falls back to the primary API if necessary.
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
        response = requests.get(PROXY_BINANCE_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logging.warning(f"Proxy failed with error: {e}. Trying primary endpoint.")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(PRIMARY_BINANCE_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logging.error(f"Primary endpoint also failed with error: {e}.")
            raise

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the specified symbol at the given target time.
    """
    # Convert target time to UTC milliseconds
    target_datetime = datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")
    target_timestamp = int(target_datetime.replace(tzinfo=pytz.UTC).timestamp() * 1000)
    
    # Fetch price data for the target time
    data = fetch_price_data(symbol, "1h", target_timestamp, target_timestamp + 3600000)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change_percentage = ((close_price - open_price) / open_price) * 100
        
        # Determine resolution based on price change
        if price_change_percentage >= 0:
            return "recommendation: p2"  # Market resolves to "Up"
        else:
            return "recommendation: p1"  # Market resolves to "Down"
    else:
        return "recommendation: p3"  # Unknown or insufficient data

def main():
    # Example usage
    symbol = "ETHUSDT"
    target_time = "2025-06-12 05:00:00"  # June 12, 2025, 5 AM ET
    result = resolve_market(symbol, target_time)
    print(result)

if __name__ == "__main__":
    main()