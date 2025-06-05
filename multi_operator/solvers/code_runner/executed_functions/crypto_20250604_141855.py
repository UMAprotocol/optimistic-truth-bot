import requests
import logging
from datetime import datetime
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

# API endpoints
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

def fetch_price(symbol, start_time, end_time):
    """
    Fetches the close price of a cryptocurrency from Binance using a proxy and primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try proxy endpoint first
        response = requests.get(PROXY_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}")
            raise

def convert_to_utc_timestamp(date_str, timezone_str):
    """
    Converts a date string with timezone to a UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    return int(utc_datetime.timestamp() * 1000)

def main():
    """
    Main function to determine if Bitcoin dominance went up or down in May 2025.
    """
    try:
        # Define the symbol and timezone
        symbol = "BTC.D"
        timezone_str = "US/Eastern"
        
        # Convert dates to UTC timestamps
        start_time = convert_to_utc_timestamp("2025-05-01 00:00", timezone_str)
        end_time = convert_to_utc_timestamp("2025-05-31 23:59", timezone_str)
        
        # Fetch prices
        start_price = fetch_price(symbol, start_time, start_time + 60000)  # 1 minute range
        end_price = fetch_price(symbol, end_time, end_time + 60000)
        
        # Determine the resolution
        if start_price < end_price:
            recommendation = "p2"  # Up
        elif start_price > end_price:
            recommendation = "p1"  # Down
        else:
            recommendation = "p3"  # 50-50
        
        print(f"recommendation: {recommendation}")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()