import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price(symbol, start_time, end_time):
    """
    Fetches the closing price of a cryptocurrency from Binance using the primary and proxy endpoints.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Proxy failed, trying primary endpoint: {e}")
        # Fallback to the primary endpoint
        response = requests.get(PRIMARY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price

def convert_to_utc(date_str, time_str, timezone_str):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    local_tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_dt = local_tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    # Define the times and symbols
    start_date = "2025-05-01"
    end_date = "2025-05-31"
    symbol = "ETHUSDT"
    timezone_str = "US/Eastern"
    
    # Convert times to UTC milliseconds
    start_time = convert_to_utc(start_date, "12:00", timezone_str)
    end_time = convert_to_utc(end_date, "23:59", timezone_str)
    
    # Fetch prices
    start_price = fetch_price(symbol, start_time, start_time + 60000)  # 1 minute range
    end_price = fetch_price(symbol, end_time, end_time + 60000)  # 1 minute range
    
    # Determine the resolution
    if start_price < end_price:
        print("recommendation: p2")  # Up
    elif start_price > end_price:
        print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # 50-50

if __name__ == "__main__":
    main()