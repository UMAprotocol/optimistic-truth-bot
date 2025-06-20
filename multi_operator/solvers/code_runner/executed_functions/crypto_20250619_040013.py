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
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logging.warning(f"Proxy failed with error: {e}. Trying primary API.")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logging.error(f"Primary API failed with error: {e}.")
            raise

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price data of the specified symbol at the target datetime.
    """
    # Convert target datetime to UTC timestamp in milliseconds
    target_timestamp_utc = int(target_datetime.timestamp() * 1000)
    
    # Fetch price data for the 1-hour interval containing the target datetime
    data = fetch_price_data(symbol, "1h", target_timestamp_utc, target_timestamp_utc + 3600000)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data available

def main():
    # Example: Solana price on June 18, 2025, 11 PM ET
    symbol = "SOLUSDT"
    target_datetime_str = "2025-06-18 23:00:00"
    timezone_str = "US/Eastern"
    
    # Convert string to datetime object in the specified timezone
    timezone = pytz.timezone(timezone_str)
    target_datetime = timezone.localize(datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S"))
    
    # Convert to UTC
    target_datetime_utc = target_datetime.astimezone(pytz.utc)
    
    # Resolve the market
    result = resolve_market(symbol, target_datetime_utc)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()