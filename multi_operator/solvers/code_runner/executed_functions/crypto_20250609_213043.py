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

def fetch_price_from_binance(symbol, start_time, end_time):
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
        print(f"Proxy failed with error {e}, trying primary endpoint.")
        # Fallback to the primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price

def convert_to_utc_timestamp(date_str, time_str, timezone_str):
    """
    Converts local time to UTC timestamp.
    """
    local_tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_dt = local_tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)  # Convert to milliseconds

def main():
    # Define the times and symbols
    start_date = "2025-05-01"
    end_date = "2025-05-31"
    symbol = "SOLETH"
    timezone_str = "US/Eastern"
    start_time_str = "12:00"
    end_time_str = "23:59"

    # Convert times to UTC timestamps
    start_timestamp = convert_to_utc_timestamp(start_date, start_time_str, timezone_str)
    end_timestamp = convert_to_utc_timestamp(end_date, end_time_str, timezone_str)

    # Fetch prices
    start_price = fetch_price_from_binance(symbol, start_timestamp, start_timestamp + 60000)  # 1 minute in milliseconds
    end_price = fetch_price_from_binance(symbol, end_timestamp, end_timestamp + 60000)

    # Determine the resolution
    if start_price < end_price:
        print("recommendation: p2")  # Up
    elif start_price > end_price:
        print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # 50-50

if __name__ == "__main__":
    main()