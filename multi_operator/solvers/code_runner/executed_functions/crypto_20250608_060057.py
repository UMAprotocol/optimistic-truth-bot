import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import pytz
import logging

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
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
        # Try fetching data from the proxy endpoint first
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logging.warning(f"Proxy API failed, error: {e}. Trying primary API...")
        try:
            # Fallback to the primary API endpoint
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logging.error(f"Primary API also failed, error: {e}.")
            return None

def get_price_change(data):
    """
    Calculate the percentage change in price from the open to the close of the candle.
    """
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        if open_price == 0:
            return None
        return ((close_price - open_price) / open_price) * 100
    return None

def main():
    # Define the specific time and date for the query
    target_date = datetime(2025, 6, 8, 1, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    start_time = int(target_date.timestamp() * 1000)
    end_time = int((target_date + timedelta(minutes=59)).timestamp() * 1000)

    # Fetch data from Binance for the BTC/USDT pair
    data = fetch_binance_data("BTCUSDT", "1h", start_time, end_time)
    if data is None:
        print("recommendation: p4")
        return

    # Calculate the price change percentage
    price_change = get_price_change(data)
    if price_change is None:
        print("recommendation: p3")
    elif price_change >= 0:
        print("recommendation: p2")
    else:
        print("recommendation: p1")

if __name__ == "__main__":
    main()