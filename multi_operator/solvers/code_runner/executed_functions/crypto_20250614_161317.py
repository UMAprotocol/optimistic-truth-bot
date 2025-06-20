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

def fetch_price_from_binance(symbol, start_time, end_time):
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
    try:
        # Define the dates, times, and timezone
        date1 = "2025-06-13"
        date2 = "2025-06-14"
        hour = 12
        minute = 0
        timezone_str = "US/Eastern"
        symbol = "SOLUSDT"

        # Convert times to UTC timestamps
        start_time1 = convert_to_utc_timestamp(date1, hour, minute, timezone_str)
        end_time1 = start_time1 + 60000  # 1 minute later in milliseconds
        start_time2 = convert_to_utc_timestamp(date2, hour, minute, timezone_str)
        end_time2 = start_time2 + 60000  # 1 minute later in milliseconds

        # Fetch prices
        price1 = fetch_price_from_binance(symbol, start_time1, end_time1)
        price2 = fetch_price_from_binance(symbol, start_time2, end_time2)

        # Determine resolution
        if price1 < price2:
            print("recommendation: p2")  # Up
        elif price1 > price2:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        logger.error(f"Failed to process due to: {e}")
        print("recommendation: p4")  # Unknown or error

if __name__ == "__main__":
    main()