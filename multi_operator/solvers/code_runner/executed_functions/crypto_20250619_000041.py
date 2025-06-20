import requests
import os
from datetime import datetime
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

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price data of the SOL/USDT pair.
    """
    # Convert target time to UTC timestamp
    eastern = pytz.timezone('US/Eastern')
    naive_dt = datetime.strptime(target_time, "%Y-%m-%d %H:%M")
    local_dt = eastern.localize(naive_dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    
    start_time = int(utc_dt.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later
    
    try:
        data = fetch_price_data(symbol, "1h", start_time, end_time)
        if data and len(data) > 0:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            if close_price >= open_price:
                return "recommendation: p2"  # Up
            else:
                return "recommendation: p1"  # Down
        else:
            return "recommendation: p3"  # Unknown/50-50
    except Exception as e:
        logging.error(f"Error resolving market: {e}")
        return "recommendation: p3"  # Unknown/50-50 due to error

def main():
    """
    Main function to execute the market resolution.
    """
    symbol = "SOLUSDT"
    target_time = "2025-06-18 19:00"
    result = resolve_market(symbol, target_time)
    print(result)

if __name__ == "__main__":
    main()