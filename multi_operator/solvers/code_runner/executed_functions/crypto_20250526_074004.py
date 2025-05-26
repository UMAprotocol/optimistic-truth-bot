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

def fetch_price_from_binance(symbol, date_str, time_str, timezone_str):
    """
    Fetches the closing price of a cryptocurrency from Binance at a specified date and time.
    """
    # Convert local time to UTC
    local_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_tz = pytz.timezone(timezone_str)
    local_dt = local_tz.localize(local_dt)
    utc_dt = local_dt.astimezone(pytz.utc)

    # Convert datetime to milliseconds since epoch
    start_time = int(utc_dt.timestamp() * 1000)
    end_time = start_time + 60000  # One minute later

    # First try the proxy endpoint
    try:
        response = requests.get(
            PROXY_API_URL,
            params={
                "symbol": symbol,
                "interval": "1m",
                "limit": 1,
                "startTime": start_time,
                "endTime": end_time
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        print(f"Proxy failed, trying primary API: {e}")

    # Fallback to the primary API endpoint
    try:
        response = requests.get(
            PRIMARY_API_URL,
            params={
                "symbol": symbol,
                "interval": "1m",
                "limit": 1,
                "startTime": start_time,
                "endTime": end_time
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        print(f"Both proxy and primary API requests failed: {e}")
        return None

def main():
    # Define the dates, times, and symbol
    symbol = "ETHUSDT"
    date1 = "2025-05-25"
    date2 = "2025-05-26"
    time_str = "12:00"
    timezone_str = "US/Eastern"

    # Fetch prices
    price1 = fetch_price_from_binance(symbol, date1, time_str, timezone_str)
    price2 = fetch_price_from_binance(symbol, date2, time_str, timezone_str)

    # Determine the resolution
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