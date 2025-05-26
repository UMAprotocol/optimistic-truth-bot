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
    Fetch the closing price of a cryptocurrency at a specific time and date from Binance.
    """
    # Convert local time to UTC
    local_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_tz = pytz.timezone(timezone_str)
    local_dt = local_tz.localize(local_dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    start_time = int(utc_dt.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 60000  # One minute later

    # Try fetching from proxy first
    try:
        response = requests.get(
            f"{PROXY_URL}/api/v3/klines",
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
    # Example usage
    symbol = "FARTCOINUSDT"
    date1 = "2025-05-22"
    date2 = "2025-05-23"
    time = "12:00"
    timezone = "US/Eastern"

    price1 = fetch_price(symbol, date1, time, timezone)
    price2 = fetch_price(symbol, date2, time, timezone)

    if price1 is None or price2 is None:
        print("recommendation: p4")
    elif price2 > price1:
        print("recommendation: p2")
    elif price2 < price1:
        print("recommendation: p1")
    else:
        print("recommendation: p3")

if __name__ == "__main__":
    main()