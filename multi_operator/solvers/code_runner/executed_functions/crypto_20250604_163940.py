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

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price(symbol, start_time, end_time):
    """
    Fetches the close price of a cryptocurrency from Binance using the proxy and falls back to the primary API if necessary.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching from the proxy endpoint
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        
        # Fallback to the primary endpoint
        try:
            response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price
        except Exception as e:
            logging.error(f"Primary endpoint also failed: {e}")
            raise

def convert_to_utc_timestamp(date_str, time_str, timezone_str):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    local_tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    local_dt = local_tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    # Define the times for price comparison
    start_date = "2025-05-01"
    start_time = "12:00:00"
    end_date = "2025-05-31"
    end_time = "23:59:00"
    timezone_str = "US/Eastern"
    symbol = "XRPUSDT"

    # Convert times to UTC timestamps
    start_timestamp = convert_to_utc_timestamp(start_date, start_time, timezone_str)
    end_timestamp = convert_to_utc_timestamp(end_date, end_time, timezone_str)

    # Fetch prices
    try:
        start_price = fetch_price(symbol, start_timestamp, start_timestamp + 60000)  # 1 minute range
        end_price = fetch_price(symbol, end_timestamp, end_timestamp + 60000)  # 1 minute range

        # Determine the resolution based on the prices
        if start_price < end_price:
            print("recommendation: p2")  # Up
        elif start_price > end_price:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        logging.error(f"Failed to fetch prices: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()