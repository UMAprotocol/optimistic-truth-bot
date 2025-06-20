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
    Fetches data from Binance API with a fallback to a proxy server if the primary request fails.
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
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logging.warning(f"Proxy API failed: {e}. Attempting primary API.")
        try:
            # Fallback to the primary API endpoint
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logging.error(f"Primary API also failed: {e}")
            raise

def analyze_price_change(data):
    """
    Analyzes the price change from the fetched data.
    """
    if not data or len(data) == 0:
        logging.error("No data available to analyze.")
        return "p3"  # Unknown or 50-50 if no data available

    open_price = float(data[0][1])
    close_price = float(data[0][4])

    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to execute the logic.
    """
    # Define the specific time and date for the analysis
    target_date = datetime(2025, 6, 14, 7, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    start_time = int(target_date.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    try:
        data = fetch_binance_data("BTCUSDT", "1h", start_time, end_time)
        result = analyze_price_change(data)
        print(f"recommendation: {result}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown or 50-50 if an error occurs

if __name__ == "__main__":
    main()