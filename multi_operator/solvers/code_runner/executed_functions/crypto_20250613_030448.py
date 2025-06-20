import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_eth_price_change(date_str, hour, minute, timezone_str):
    """
    Fetches the percentage change for the ETH/USDT pair from Binance for a specific hour candle.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format
        minute: Minute
        timezone_str: Timezone string

    Returns:
        float: Percentage change of ETH/USDT
    """
    # Convert local time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    local_dt = tz.localize(datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S"))
    utc_dt = local_dt.astimezone(pytz.utc)
    start_time = int(utc_dt.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # Function to make API requests
    def make_request(url):
        params = {
            "symbol": "ETHUSDT",
            "interval": "1h",
            "startTime": start_time,
            "endTime": end_time,
            "limit": 1
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return ((close_price - open_price) / open_price) * 100
        return None

    # Try proxy endpoint first
    try:
        return make_request(f"{PROXY_BINANCE_API}/klines")
    except Exception as e:
        print(f"Proxy failed: {e}, trying primary endpoint.")
        # Fallback to primary endpoint
        try:
            return make_request(f"{PRIMARY_BINANCE_API}/klines")
        except Exception as e:
            print(f"Primary endpoint failed: {e}")
            return None

def main():
    # Specific date and time for the query
    date_str = "2025-06-12"
    hour = 22  # 10 PM
    minute = 0
    timezone_str = "US/Eastern"

    # Fetch the percentage change
    change = fetch_eth_price_change(date_str, hour, minute, timezone_str)

    # Determine the resolution based on the change
    if change is None:
        print("recommendation: p4")  # Unable to determine
    elif change >= 0:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

if __name__ == "__main__":
    main()