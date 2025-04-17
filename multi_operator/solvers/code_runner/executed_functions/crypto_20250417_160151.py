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
    Fetches the price data from Binance API with a fallback to a proxy endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
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
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    return None

def convert_to_utc_timestamp(date_str, time_str, timezone_str):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(timezone_str)
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    dt_local = tz.localize(dt)
    dt_utc = dt_local.astimezone(pytz.utc)
    return int(dt_utc.timestamp() * 1000)

def main():
    # Define the dates, times, and timezone
    date1 = "2025-04-16"
    date2 = "2025-04-17"
    time_str = "12:00:00"
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"

    # Convert times to UTC timestamps
    start_time1 = convert_to_utc_timestamp(date1, time_str, timezone_str)
    end_time1 = start_time1 + 60000  # 1 minute later in milliseconds
    start_time2 = convert_to_utc_timestamp(date2, time_str, timezone_str)
    end_time2 = start_time2 + 60000  # 1 minute later in milliseconds

    # Fetch prices
    price1 = fetch_price(symbol, "1m", start_time1, end_time1)
    price2 = fetch_price(symbol, "1m", start_time2, end_time2)

    # Determine the resolution
    if price1 is not None and price2 is not None:
        if price2 > price1:
            print("recommendation: p2")  # Up
        elif price2 < price1:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    else:
        print("recommendation: p4")  # Unknown or data fetch error

if __name__ == "__main__":
    main()