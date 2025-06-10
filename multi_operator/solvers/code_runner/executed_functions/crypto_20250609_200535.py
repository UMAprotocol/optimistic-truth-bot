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

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
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
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}. Falling back to primary endpoint.")
        try:
            # Fallback to the primary endpoint
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logging.error(f"Both endpoints failed: {e}")
            raise

def analyze_candle_data(candle_data):
    """
    Analyzes the candle data to determine if the price went up or down.
    """
    if not candle_data or len(candle_data) < 1 or len(candle_data[0]) < 5:
        logging.error("Invalid candle data received.")
        return "p3"  # Unknown/50-50 if data is insufficient

    open_price = float(candle_data[0][1])
    close_price = float(candle_data[0][4])

    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to process the market resolution for Bitcoin price movement.
    """
    symbol = "BTCUSDT"
    interval = "1h"
    target_date = datetime(2025, 5, 30, 11, 0, 0, tzinfo=pytz.timezone("America/New_York"))
    start_time = int(target_date.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    try:
        candle_data = fetch_binance_data(symbol, interval, start_time, end_time)
        resolution = analyze_candle_data(candle_data)
        print(f"recommendation: {resolution}")
    except Exception as e:
        logging.error(f"Error processing the market resolution: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there is an error

if __name__ == "__main__":
    main()