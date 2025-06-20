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
        logging.error(f"Proxy API failed: {e}. Attempting primary API.")
        try:
            # Fallback to the primary API endpoint
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logging.error(f"Primary API also failed: {e}.")
            raise

def get_eth_price_change():
    """
    Determines if the price of ETH/USDT has gone up or down at the specified time.
    """
    # Define the specific time and date
    target_datetime = datetime(2025, 6, 12, 0, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    target_timestamp = int(target_datetime.timestamp() * 1000)  # Convert to milliseconds

    # Fetch the 1-hour candle data for ETH/USDT starting at the specified time
    try:
        data = fetch_binance_data("ETHUSDT", "1h", target_timestamp, target_timestamp + 3600000)
        if data and len(data) > 0:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            price_change = close_price - open_price
            recommendation = "p2" if price_change < 0 else "p1"
            logging.info(f"ETH/USDT price change: {price_change} (Open: {open_price}, Close: {close_price})")
            return f"recommendation: {recommendation}"
        else:
            logging.error("No data available for the specified time.")
            return "recommendation: p3"
    except Exception as e:
        logging.error(f"Error fetching or processing data: {e}")
        return "recommendation: p3"

if __name__ == "__main__":
    result = get_eth_price_change()
    print(result)