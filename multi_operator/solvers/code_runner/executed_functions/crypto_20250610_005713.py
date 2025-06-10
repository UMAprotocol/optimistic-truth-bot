import requests
import logging
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price(symbol, start_time, end_time):
    """
    Fetches the closing price of a cryptocurrency from Binance using the proxy and falls back to the primary API if necessary.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching from proxy first
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        logger.error(f"Proxy failed with error: {e}, trying primary API.")
        try:
            # Fallback to primary API
            response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price
        except Exception as e:
            logger.error(f"Primary API also failed with error: {e}")
            raise

def convert_to_utc_timestamp(date_str, hour, minute, timezone_str):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {hour}:{minute}", "%Y-%m-%d %H:%M")
    local_dt = tz.localize(local_time)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    """
    Main function to determine if the price of Ethereum on Binance went up or down between two specific times.
    """
    try:
        # Define the times to check
        start_time = convert_to_utc_timestamp("2025-05-30", 12, 0, "US/Eastern")
        end_time = convert_to_utc_timestamp("2025-05-31", 12, 0, "US/Eastern")
        
        # Fetch prices
        price_day1 = fetch_price("ETHUSDT", start_time, start_time + 60000)  # 1 minute later
        price_day2 = fetch_price("ETHUSDT", end_time, end_time + 60000)  # 1 minute later
        
        # Determine the resolution
        if price_day1 < price_day2:
            print("recommendation: p2")  # Up
        elif price_day1 > price_day2:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        logger.error(f"Failed to resolve due to error: {e}")
        print("recommendation: p4")  # Unknown or error

if __name__ == "__main__":
    main()