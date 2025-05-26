import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API URLs
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price(symbol, date_str, hour, minute, timezone_str):
    """
    Fetch the close price of a cryptocurrency at a specific time from Binance API.
    """
    # Convert local time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
    local_time = tz.localize(local_time)
    utc_time = local_time.astimezone(pytz.utc)
    timestamp = int(utc_time.timestamp() * 1000)  # Convert to milliseconds

    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 60000  # 1 minute later
    }

    try:
        # Try fetching from the proxy API first
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        logging.warning(f"Proxy API failed, trying primary API: {e}")
        # If proxy fails, try the primary API
        response = requests.get(PRIMARY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price

def resolve_market():
    """
    Resolve the market based on the close prices of FARTCOIN-USD on two specific dates.
    """
    symbol = "FARTCOINUSDT"
    date1 = "2025-05-23"
    date2 = "2025-05-24"
    hour = 12
    minute = 0
    timezone_str = "US/Eastern"

    try:
        price1 = fetch_price(symbol, date1, hour, minute, timezone_str)
        price2 = fetch_price(symbol, date2, hour, minute, timezone_str)
        if price1 < price2:
            return "recommendation: p2"  # Up
        elif price1 > price2:
            return "recommendation: p1"  # Down
        else:
            return "recommendation: p3"  # 50-50
    except Exception as e:
        logging.error(f"Error resolving market: {e}")
        return "recommendation: p4"  # Unable to resolve

if __name__ == "__main__":
    result = resolve_market()
    print(result)