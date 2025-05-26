import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

def fetch_price(symbol, date_str, time_str, timezone_str):
    """
    Fetches the closing price of a cryptocurrency at a specific time and date from Binance.
    """
    # Convert local time to UTC
    local_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_tz = pytz.timezone(timezone_str)
    local_dt = local_tz.localize(local_dt)
    utc_dt = local_dt.astimezone(pytz.utc)

    # Convert datetime to milliseconds since epoch
    start_time = int(utc_dt.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later

    # Try fetching from proxy first
    try:
        response = requests.get(
            f"{PROXY_URL}/klines",
            params={
                "symbol": symbol,
                "interval": "1m",
                "startTime": start_time,
                "endTime": end_time,
                "limit": 1
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Proxy failed, trying primary endpoint: {e}")

    # Fallback to primary endpoint
    try:
        response = requests.get(
            f"{PRIMARY_URL}/klines",
            params={
                "symbol": symbol,
                "interval": "1m",
                "startTime": start_time,
                "endTime": end_time,
                "limit": 1
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Primary endpoint failed: {e}")
        return None

def main():
    # Define the symbol and times
    symbol = "FARTCOINUSDT"
    date1 = "2025-05-23"
    time1 = "12:00"
    date2 = "2025-05-24"
    time2 = "12:00"
    timezone_str = "US/Eastern"

    # Fetch prices
    price1 = fetch_price(symbol, date1, time1, timezone_str)
    price2 = fetch_price(symbol, date2, time2, timezone_str)

    # Determine resolution
    if price1 is not None and price2 is not None:
        if price1 < price2:
            print("recommendation: p2")  # Up
        elif price1 > price2:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    else:
        print("recommendation: p4")  # Unknown

if __name__ == "__main__":
    main()