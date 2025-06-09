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

def fetch_price_from_binance(symbol, start_time, end_time):
    """
    Fetches the closing price of a cryptocurrency from Binance using the proxy and falls back to the primary API if necessary.
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
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary API.")
        try:
            # Fallback to the primary API endpoint
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def get_unix_time_ms(year, month, day, hour, minute, tz_name):
    """
    Converts a given date and time to UTC Unix time in milliseconds.
    """
    tz = pytz.timezone(tz_name)
    dt = datetime(year, month, day, hour, minute)
    dt_local = tz.localize(dt)
    dt_utc = dt_local.astimezone(pytz.utc)
    return int(dt_utc.timestamp() * 1000)

def main():
    # Specific date and time for the query
    year, month, day = 2025, 6, 6
    hour, minute = 12, 0  # Noon
    tz_name = "US/Eastern"
    symbol = "SOLUSDT"
    threshold_price = 200.01

    # Convert the specific time to Unix time in milliseconds
    start_time = get_unix_time_ms(year, month, day, hour, minute, tz_name)
    end_time = start_time + 60000  # Plus one minute

    # Fetch the closing price from Binance
    close_price = fetch_price_from_binance(symbol, start_time, end_time)

    # Determine the resolution based on the fetched price
    if close_price is None:
        print("recommendation: p4")  # Unable to fetch price
    elif close_price >= threshold_price:
        print("recommendation: p2")  # Yes, price is above threshold
    else:
        print("recommendation: p1")  # No, price is below threshold

if __name__ == "__main__":
    main()