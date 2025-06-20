import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
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
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logging.warning(f"Proxy failed with error: {e}. Trying primary endpoint.")
        # Fallback to the primary endpoint if proxy fails
        response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from primary endpoint.")
        return data

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the open and close prices of the specified symbol at the target datetime.
    """
    # Convert target datetime to UTC timestamp in milliseconds
    target_timestamp_utc = int(target_datetime.timestamp() * 1000)
    
    # Fetch data for the specific minute
    data = fetch_binance_data(symbol, "1h", target_timestamp_utc, target_timestamp_utc + 3600000)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        logging.info(f"Open price: {open_price}, Close price: {close_price}")
        
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        logging.error("No data available for the specified time.")
        return "p3"  # Unknown/50-50

def main():
    # Example: June 18, 2025, 7 PM ET
    target_date_str = "2025-06-18"
    target_hour = 19  # 7 PM
    target_timezone = "US/Eastern"
    
    # Convert local time to UTC
    local_tz = pytz.timezone(target_timezone)
    naive_datetime = datetime.strptime(target_date_str + f" {target_hour}:00:00", "%Y-%m-%d %H:%M:%S")
    local_datetime = local_tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    
    # Symbol for the market
    symbol = "BTCUSDT"
    
    # Resolve the market
    result = resolve_market(symbol, utc_datetime)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()