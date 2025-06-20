import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_eth_price(date_str, hour, minute, timezone_str):
    """
    Fetches the ETH/USDT price data for a specific hour and minute on a given date.
    """
    # Convert local time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    local_dt = tz.localize(datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S"))
    utc_dt = local_dt.astimezone(pytz.utc)
    start_time = int(utc_dt.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # Try fetching data from the proxy endpoint first
    try:
        response = requests.get(
            f"{PROXY_API_URL}?symbol=ETHUSDT&interval=1h&limit=1&startTime={start_time}&endTime={end_time}",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return open_price, close_price
    except Exception as e:
        print(f"Proxy failed, error: {e}, trying primary API...")

    # Fallback to the primary API if proxy fails
    try:
        response = requests.get(
            f"{PRIMARY_API_URL}/klines",
            params={
                "symbol": "ETHUSDT",
                "interval": "1h",
                "limit": "1",
                "startTime": start_time,
                "endTime": end_time
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return open_price, close_price
    except Exception as e:
        print(f"Primary API failed, error: {e}")
        return None, None

def main():
    # Specific date and time for the query
    date_str = "2025-06-18"
    hour = 13  # 1 PM ET
    minute = 0
    timezone_str = "US/Eastern"

    open_price, close_price = fetch_eth_price(date_str, hour, minute, timezone_str)
    if open_price is not None and close_price is not None:
        if close_price >= open_price:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data fetch failure

if __name__ == "__main__":
    main()