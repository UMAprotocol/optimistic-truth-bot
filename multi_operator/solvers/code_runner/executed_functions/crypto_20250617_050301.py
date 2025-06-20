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
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_eth_price_change(date_str, hour=0, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the percentage change for the ETH/USDT pair for a specific hour candle on Binance.
    """
    # Convert local time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
    local_time = tz.localize(local_time)
    utc_time = local_time.astimezone(pytz.utc)
    start_time_ms = int(utc_time.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later in milliseconds

    # Construct the URL with parameters
    params = {
        "symbol": "ETHUSDT",
        "interval": "1h",
        "startTime": start_time_ms,
        "endTime": end_time_ms,
        "limit": 1
    }

    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logging.warning(f"Proxy failed, error: {e}. Trying primary endpoint.")
        # Fallback to the primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logging.error(f"Both proxy and primary endpoints failed: {e}")
            return None

    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        change_percent = ((close_price - open_price) / open_price) * 100
        return change_percent
    else:
        logging.error("No data returned from Binance API.")
        return None

def main():
    # Specific date and time for the market question
    date_str = "2025-06-17"
    hour = 0  # 12 AM ET
    timezone_str = "US/Eastern"

    # Fetch the price change
    change_percent = fetch_eth_price_change(date_str, hour, timezone_str=timezone_str)

    # Determine the resolution based on the change percentage
    if change_percent is None:
        print("recommendation: p3")  # Unknown or API failure
    elif change_percent >= 0:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

if __name__ == "__main__":
    main()