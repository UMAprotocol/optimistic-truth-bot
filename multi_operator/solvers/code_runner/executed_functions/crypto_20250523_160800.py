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

    # Prepare API request
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 60000  # 1 minute later
    }

    # Try fetching from proxy first
    try:
        response = requests.get(f"{PROXY_URL}/klines", params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        print(f"Proxy failed, trying primary endpoint: {e}")

    # Fallback to primary endpoint
    try:
        response = requests.get(f"{PRIMARY_URL}/klines", params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        print(f"Both proxy and primary requests failed: {e}")
        return None

def main():
    # Example dates and times
    date1 = "2025-05-22"
    date2 = "2025-05-23"
    time = "12:00"
    timezone = "US/Eastern"
    symbol = "FARTCOINUSDT"

    # Fetch prices
    price1 = fetch_price(symbol, date1, time, timezone)
    price2 = fetch_price(symbol, date2, time, timezone)

    # Determine resolution
    if price1 is None or price2 is None:
        print("recommendation: p4")  # Unable to fetch prices
    elif price2 > price1:
        print("recommendation: p1")  # Price went up
    elif price2 < price1:
        print("recommendation: p2")  # Price went down
    else:
        print("recommendation: p3")  # Prices are equal

if __name__ == "__main__":
    main()