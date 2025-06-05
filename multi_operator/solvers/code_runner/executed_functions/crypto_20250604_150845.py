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

def fetch_price(symbol, date_str, hour, minute, timezone_str):
    """
    Fetches the closing price of a cryptocurrency from Binance at a specified date and time.
    """
    # Convert local time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    naive_dt = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
    local_dt = tz.localize(naive_dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    timestamp = int(utc_dt.timestamp() * 1000)  # Convert to milliseconds

    # Prepare parameters for API request
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 60000  # 1 minute later
    }

    # Try fetching data from the proxy endpoint first
    try:
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])  # Closing price is the fifth element
        return close_price
    except Exception as e:
        print(f"Proxy failed, error: {e}, falling back to primary endpoint")

    # Fallback to the primary endpoint if proxy fails
    try:
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])  # Closing price is the fifth element
        return close_price
    except Exception as e:
        print(f"Primary endpoint also failed, error: {e}")
        raise

def main():
    # Define the symbol and times for the price checks
    symbol = "SOLUSDT"
    first_date = "2025-05-31"
    second_date = "2025-06-01"
    hour = 12
    minute = 0
    timezone_str = "US/Eastern"

    try:
        # Fetch prices at the specified times
        first_price = fetch_price(symbol, first_date, hour, minute, timezone_str)
        second_price = fetch_price(symbol, second_date, hour, minute, timezone_str)

        # Determine the resolution based on the prices
        if first_price < second_price:
            print("recommendation: p2")  # Up
        elif first_price > second_price:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        print(f"Failed to fetch prices or determine resolution, error: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()