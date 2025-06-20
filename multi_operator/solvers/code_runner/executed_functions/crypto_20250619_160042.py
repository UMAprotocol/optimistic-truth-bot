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

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
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
        response = requests.get(f"{PROXY_API}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logging.warning(f"Proxy API failed: {e}. Attempting primary API.")
        # Fallback to primary API if proxy fails
        response = requests.get(f"{PRIMARY_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from primary API.")
        return data

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price data of the specified symbol at the target time.
    """
    # Convert target time to UTC milliseconds
    target_time_utc = int(target_time.timestamp() * 1000)
    
    # Fetch price data
    data = fetch_price_data(symbol, "1h", target_time_utc, target_time_utc + 3600000)  # 1 hour in milliseconds
    
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        logging.info(f"Open price: {open_price}, Close price: {close_price}")
        
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        logging.error("No data available to resolve the market.")
        return "p3"  # Unknown/50-50

def main():
    """
    Main function to execute the market resolution.
    """
    # Define the symbol and target time
    symbol = "ETHUSDT"
    target_time = datetime(2025, 6, 19, 11, 0, tzinfo=pytz.timezone("US/Eastern"))
    
    # Resolve the market
    result = resolve_market(symbol, target_time)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()