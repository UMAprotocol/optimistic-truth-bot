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
PRIMARY_API = "https://api.binance.com/api/v3"
PROXY_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try fetching data from the proxy API first
        response = requests.get(f"{PROXY_API}", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched from proxy API.")
        return data
    except Exception as e:
        logging.error(f"Proxy API failed: {e}, trying primary API.")
        # If proxy fails, fallback to the primary API
        try:
            response = requests.get(f"{PRIMARY_API}/klines", params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched from primary API.")
            return data
        except Exception as e:
            logging.error(f"Primary API failed: {e}")
            raise

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the opening and closing prices of the specified symbol at the target time.
    """
    # Convert target time to UTC milliseconds
    target_datetime = datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")
    target_utc = target_datetime.replace(tzinfo=pytz.utc)
    start_time = int(target_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch data
    data = fetch_binance_data(symbol, "1h", start_time, end_time)

    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        logging.info(f"Open price: {open_price}, Close price: {close_price}")

        # Determine resolution
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    # Example usage
    symbol = "BTCUSDT"
    target_time = "2025-06-19 00:00:00"
    result = resolve_market(symbol, target_time)
    print(result)

if __name__ == "__main__":
    main()