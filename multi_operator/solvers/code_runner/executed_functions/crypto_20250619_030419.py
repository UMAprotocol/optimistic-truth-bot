import requests
import os
from datetime import datetime
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

def fetch_eth_price(date_str, hour, minute, timezone_str):
    """
    Fetches the ETH/USDT price for a specific hour and minute on a given date.
    """
    # Convert local time to UTC
    tz = pytz.timezone(timezone_str)
    naive_dt = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
    local_dt = tz.localize(naive_dt)
    utc_dt = local_dt.astimezone(pytz.utc)

    # Convert datetime to milliseconds since epoch
    start_time = int(utc_dt.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Prepare API request
    params = {
        "symbol": "ETHUSDT",
        "interval": "1h",
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }

    try:
        # Try fetching from proxy API first
        response = requests.get(f"{PROXY_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy API.")
    except Exception as e:
        logging.error(f"Proxy API failed: {e}, trying primary API.")
        # Fallback to primary API if proxy fails
        try:
            response = requests.get(f"{PRIMARY_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
        except Exception as e:
            logging.error(f"Primary API also failed: {e}")
            return None

    # Extract open and close prices
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        logging.error("No data available for the specified time.")
        return None

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the open and close prices.
    """
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    # Specific date and time for the market resolution
    date_str = "2025-06-18"
    hour = 22  # 10 PM
    minute = 0
    timezone_str = "US/Eastern"

    # Fetch ETH prices
    prices = fetch_eth_price(date_str, hour, minute, timezone_str)
    if prices:
        open_price, close_price = prices
        # Resolve the market
        resolution = resolve_market(open_price, close_price)
        print(f"recommendation: {resolution}")
    else:
        print("recommendation: p3")  # Unknown/50-50 if no data could be fetched

if __name__ == "__main__":
    main()