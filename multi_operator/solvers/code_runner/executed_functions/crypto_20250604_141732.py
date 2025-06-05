import requests
import logging
from datetime import datetime
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Binance API URLs
PRIMARY_BINANCE_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price(symbol, start_time, end_time):
    """
    Fetches the price from Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching from the proxy first
        response = requests.get(PROXY_BINANCE_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        logging.warning(f"Proxy failed with error: {e}. Trying primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_BINANCE_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price
        except Exception as e:
            logging.error(f"Primary API failed with error: {e}")
            raise

def convert_to_utc_timestamp(date_str, timezone_str="America/New_York"):
    """
    Converts a date string to a UTC timestamp.
    """
    local_tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    local_datetime = local_tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    return int(utc_datetime.timestamp() * 1000)

def main():
    """
    Main function to determine if Bitcoin dominance went up or down in May 2025.
    """
    try:
        start_price_time = convert_to_utc_timestamp("2025-05-01 00:00")
        end_price_time = convert_to_utc_timestamp("2025-05-31 23:59")
        
        start_price = fetch_price("BTCUSDT", start_price_time, start_price_time + 60000)
        end_price = fetch_price("BTCUSDT", end_price_time, end_price_time + 60000)
        
        if start_price < end_price:
            print("recommendation: p2")  # Up
        elif start_price > end_price:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        logging.error(f"Failed to resolve the market due to: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()