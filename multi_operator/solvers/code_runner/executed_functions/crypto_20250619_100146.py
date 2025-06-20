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

def get_binance_data(symbol, interval, start_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    primary_url = "https://api.binance.com/api/v3/klines"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }
    
    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched from proxy endpoint.")
        return data
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}. Falling back to primary endpoint.")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(primary_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched from primary endpoint.")
        return data

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the open and close prices of the specified candle.
    """
    # Convert target time to UTC milliseconds
    target_time_utc = int(target_time.timestamp() * 1000)
    
    # Fetch data
    data = get_binance_data(symbol, "1h", target_time_utc)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data

def main():
    """
    Main function to handle the resolution of the market.
    """
    # Define the symbol and the specific time for the market
    symbol = "BTCUSDT"
    target_time_str = "2025-06-19 05:00:00"
    timezone_str = "US/Eastern"
    
    # Convert the target time to a datetime object
    tz = pytz.timezone(timezone_str)
    target_time = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
    target_time = tz.localize(target_time)
    
    # Resolve the market
    resolution = resolve_market(symbol, target_time)
    
    # Output the recommendation
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()