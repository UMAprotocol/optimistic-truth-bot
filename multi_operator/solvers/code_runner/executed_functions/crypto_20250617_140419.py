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
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logging.warning(f"Proxy failed with error: {e}. Trying primary API.")
        try:
            # Fallback to the primary API endpoint
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logging.error(f"Both proxy and primary API requests failed: {e}")
            return None

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the symbol at the specified target time.
    """
    # Convert target time to UTC milliseconds
    target_datetime = datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")
    target_timestamp = int(target_datetime.replace(tzinfo=pytz.UTC).timestamp() * 1000)
    
    # Fetch price data for the target time
    data = fetch_price_data(symbol, "1h", target_timestamp, target_timestamp + 3600000)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = close_price - open_price
        
        if price_change >= 0:
            logging.info("Market resolves to 'Up'.")
            return "recommendation: p2"  # p2 corresponds to 'Up'
        else:
            logging.info("Market resolves to 'Down'.")
            return "recommendation: p1"  # p1 corresponds to 'Down'
    else:
        logging.warning("No data available to resolve the market.")
        return "recommendation: p3"  # p3 corresponds to unknown/50-50

def main():
    # Example usage
    symbol = "BTCUSDT"
    target_time = "2025-06-17 09:00:00"  # Example target time
    result = resolve_market(symbol, target_time)
    print(result)

if __name__ == "__main__":
    main()