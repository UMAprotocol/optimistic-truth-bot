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
PRIMARY_BINANCE_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_BINANCE_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_btc_data(start_time, end_time):
    """
    Fetches BTC data from Binance API between specified start and end times.
    Implements a fallback from proxy to primary endpoint.
    """
    params = {
        'symbol': 'BTCUSDT',
        'interval': '1d',
        'startTime': start_time,
        'endTime': end_time
    }
    try:
        # Try fetching from proxy endpoint
        response = requests.get(f"{PROXY_BINANCE_ENDPOINT}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logging.error(f"Failed to fetch from proxy endpoint: {e}. Trying primary endpoint.")
        try:
            # Fallback to primary endpoint
            response = requests.get(f"{PRIMARY_BINANCE_ENDPOINT}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logging.error(f"Failed to fetch from primary endpoint: {e}")
            return None

def analyze_btc_purchases(data):
    """
    Analyzes the fetched BTC data to determine if MicroStrategy purchased more than 8000 BTC.
    """
    total_btc_purchased = sum([float(item[5]) for item in data])  # Summing up the volume of BTC
    logging.info(f"Total BTC purchased: {total_btc_purchased}")
    return total_btc_purchased >= 8001

def main():
    # Define the time period for the query
    start_date = datetime(2025, 6, 10, 0, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 6, 16, 23, 59, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Convert datetime to milliseconds since epoch
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)
    
    # Fetch BTC data
    btc_data = fetch_btc_data(start_time, end_time)
    
    if btc_data is None:
        logging.error("No data available to analyze.")
        print("recommendation: p4")
        return
    
    # Analyze BTC purchases
    if analyze_btc_purchases(btc_data):
        print("recommendation: p2")  # MicroStrategy purchased more than 8000 BTC
    else:
        print("recommendation: p1")  # MicroStrategy did not purchase more than 8000 BTC

if __name__ == "__main__":
    main()