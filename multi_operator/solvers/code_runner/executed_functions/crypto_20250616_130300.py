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
        # Try fetching from proxy first
        response = requests.get(f"{PROXY_API}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logging.warning(f"Proxy failed, error: {e}. Trying primary API.")
        try:
            # Fallback to primary API
            response = requests.get(f"{PRIMARY_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logging.error(f"Both proxy and primary API failed, error: {e}.")
            return None

def analyze_price_change(data):
    """
    Analyzes the price change from the fetched data.
    """
    if not data or len(data) < 1:
        logging.error("No data available to analyze.")
        return "p4"
    
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
    # Define the specific time and date
    target_date = datetime(2025, 6, 16, 8, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    start_time = int(target_date.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    # Fetch the price data
    data = fetch_price_data("BTCUSDT", "1h", start_time, end_time)

    # Analyze the price change
    result = analyze_price_change(data)

    # Print the recommendation
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()