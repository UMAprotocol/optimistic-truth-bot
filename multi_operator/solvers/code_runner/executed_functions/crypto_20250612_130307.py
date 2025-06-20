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
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy failed with error: {e}, falling back to primary API.")
        # Fallback to the primary API endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def get_utc_timestamp(year, month, day, hour, minute, tz_name):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    local_tz = pytz.timezone(tz_name)
    local_time = local_tz.localize(datetime(year, month, day, hour, minute))
    utc_time = local_time.astimezone(pytz.utc)
    return int(utc_time.timestamp() * 1000)

def main():
    # Specific date and time for the event
    year, month, day = 2025, 6, 12
    hour, minute = 8, 0  # 8 AM ET
    tz_name = "US/Eastern"
    symbol = "BTCUSDT"
    interval = "1h"

    # Convert event time to UTC timestamp
    start_time = get_utc_timestamp(year, month, day, hour, minute, tz_name)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    # Fetch price data
    data = fetch_price_data(symbol, interval, start_time, end_time)
    if data:
        open_price = float(data[1])
        close_price = float(data[4])
        price_change_percentage = ((close_price - open_price) / open_price) * 100

        # Determine the resolution based on price change
        if price_change_percentage >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 if data is not available

if __name__ == "__main__":
    main()