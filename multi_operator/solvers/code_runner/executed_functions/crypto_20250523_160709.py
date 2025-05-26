import requests
import os
from datetime import datetime
from pytz import timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price(symbol, date_str, time_str, tz_str):
    """
    Fetch the closing price of a cryptocurrency at a specific time and date.
    """
    # Convert local time to UTC
    local_tz = timezone(tz_str)
    naive_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_datetime = local_tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(timezone('UTC'))
    timestamp = int(utc_datetime.timestamp() * 1000)  # Convert to milliseconds

    # Prepare API request
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 60000  # 1 minute later
    }

    # Try proxy endpoint first
    try:
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])  # Closing price
        return close_price
    except Exception as e:
        print(f"Proxy failed, trying primary endpoint: {e}")

    # Fallback to primary endpoint
    try:
        response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])  # Closing price
        return close_price
    except Exception as e:
        print(f"Both proxy and primary endpoints failed: {e}")
        return None

def main():
    # Define the symbols and times based on the market question
    symbol = "FARTCOINUSDT"
    date1 = "2025-05-22"
    date2 = "2025-05-23"
    time = "12:00"
    tz_str = "US/Eastern"

    # Fetch prices
    price1 = fetch_price(symbol, date1, time, tz_str)
    price2 = fetch_price(symbol, date2, time, tz_str)

    # Determine the resolution
    if price1 is not None and price2 is not None:
        if price1 < price2:
            print("recommendation: p2")  # Up
        elif price1 > price2:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    else:
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()