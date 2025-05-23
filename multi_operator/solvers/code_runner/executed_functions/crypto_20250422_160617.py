import requests
import os
from datetime import datetime, timedelta, timezone
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
        print(f"Proxy failed with error: {e}, trying primary API.")
        try:
            # Fallback to primary API
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def convert_to_utc_timestamp(date_str, hour, minute, tz_str):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(tz_str)
    local_dt = tz.localize(datetime.strptime(date_str, "%Y-%m-%d"))
    local_dt = local_dt.replace(hour=hour, minute=minute)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    # Define the dates and times for price comparison
    date1 = "2025-04-21"
    date2 = "2025-04-22"
    hour = 12
    minute = 0
    tz_str = "US/Eastern"
    symbol = "BTCUSDT"
    
    # Convert dates and times to UTC timestamps
    start_time1 = convert_to_utc_timestamp(date1, hour, minute, tz_str)
    end_time1 = start_time1 + 60000  # 1 minute later in milliseconds
    start_time2 = convert_to_utc_timestamp(date2, hour, minute, tz_str)
    end_time2 = start_time2 + 60000  # 1 minute later in milliseconds
    
    # Fetch prices
    price1 = fetch_price(symbol, "1m", start_time1, end_time1)
    price2 = fetch_price(symbol, "1m", start_time2, end_time2)
    
    # Determine the resolution based on prices
    if price1 is not None and price2 is not None:
        if price2 > price1:
            print("recommendation: p2")  # Up
        elif price2 < price1:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    else:
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()