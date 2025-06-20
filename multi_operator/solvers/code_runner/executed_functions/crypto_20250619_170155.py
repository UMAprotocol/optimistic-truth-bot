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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Binance API endpoints
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3/klines"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint.
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
        response = requests.get(PROXY_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logging.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to the primary endpoint
        response = requests.get(PRIMARY_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from primary endpoint.")
        return data

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the open and close prices of the specified symbol at the target time.
    """
    # Convert target time to UTC milliseconds
    target_time_utc = int(target_time.timestamp() * 1000)
    
    # Fetch data for the specific minute
    data = fetch_binance_data(symbol, "1h", target_time_utc, target_time_utc + 60000)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    """
    Main function to handle the resolution of the market.
    """
    # Define the symbol and the specific time for the market resolution
    symbol = "BTCUSDT"
    target_time_str = "2025-06-19 12:00:00"
    timezone_str = "US/Eastern"
    
    # Convert string time to datetime object in the specified timezone
    timezone = pytz.timezone(timezone_str)
    target_time = timezone.localize(datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S"))
    
    # Resolve the market
    result = resolve_market(symbol, target_time)
    print(result)

if __name__ == "__main__":
    main()