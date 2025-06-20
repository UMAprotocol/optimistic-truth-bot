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
PRIMARY_API_ENDPOINT = "https://api.binance.com/api/v3/klines"
PROXY_API_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy endpoint.
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
        response = requests.get(PROXY_API_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}. Falling back to primary endpoint.")
        # Fallback to the primary endpoint
        try:
            response = requests.get(PRIMARY_API_ENDPOINT, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logging.error(f"Both endpoints failed: {e}")
            return None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of the symbol at the specified datetime.
    """
    # Convert datetime to the correct format for the API call
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later in milliseconds

    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = close_price - open_price

        if price_change >= 0:
            logging.info(f"Market resolves to 'Up'. Open: {open_price}, Close: {close_price}")
            return "recommendation: p2"  # Up
        else:
            logging.info(f"Market resolves to 'Down'. Open: {open_price}, Close: {close_price}")
            return "recommendation: p1"  # Down
    else:
        logging.error("No data available to resolve the market.")
        return "recommendation: p3"  # Unknown/50-50

def main():
    # Example usage
    symbol = "ETHUSDT"
    target_datetime = datetime(2025, 6, 11, 5, 0, tzinfo=pytz.timezone("US/Eastern"))
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()