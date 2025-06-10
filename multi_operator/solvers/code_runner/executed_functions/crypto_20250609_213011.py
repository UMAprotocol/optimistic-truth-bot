import requests
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price(symbol, interval, start_time, end_time):
    """
    Fetches the price data from Binance using the proxy and falls back to the primary API if necessary.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching from proxy first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Proxy failed with error {e}, trying primary API.")
        try:
            # Fallback to primary API
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price
        except Exception as e:
            print(f"Primary API also failed with error {e}.")
            return None

def convert_to_utc_timestamp(date_str, time_str, timezone_str):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    local_tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    local_dt = local_tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    # Define the symbol and the times to check
    symbol = "SOL/ETH"
    start_date = "2025-05-01"
    end_date = "2025-05-31"
    start_time_str = "12:00:00"
    end_time_str = "23:59:00"
    timezone_str = "US/Eastern"

    # Convert times to UTC timestamps
    start_timestamp = convert_to_utc_timestamp(start_date, start_time_str, timezone_str)
    end_timestamp = convert_to_utc_timestamp(end_date, end_time_str, timezone_str)

    # Fetch prices
    start_price = fetch_price(symbol, "1m", start_timestamp, start_timestamp + 60000)
    end_price = fetch_price(symbol, "1m", end_timestamp, end_timestamp + 60000)

    # Determine the resolution based on prices
    if start_price is not None and end_price is not None:
        if end_price > start_price:
            print("recommendation: p2")  # Up
        elif end_price < start_price:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    else:
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()