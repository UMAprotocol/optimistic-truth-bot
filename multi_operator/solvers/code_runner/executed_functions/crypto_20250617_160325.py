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

def fetch_price(symbol, date_str, hour=12, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the closing price of a cryptocurrency from Binance at a specified date and time.
    """
    # Convert local time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
    local_dt = tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    timestamp = int(utc_dt.timestamp() * 1000)  # Convert to milliseconds

    # Parameters for API request
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 60000  # 1 minute later
    }

    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        print(f"Proxy failed, error: {e}, trying primary API...")
        # Fallback to primary API if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            close_price = float(data[0][4])
            return close_price
        except Exception as e:
            print(f"Primary API also failed, error: {e}")
            return None

def main():
    # Define the symbols and times based on the provided question
    symbol = "SOLUSDT"
    date1 = "2025-06-16"
    date2 = "2025-06-17"
    hour = 12  # Noon

    # Fetch prices
    price1 = fetch_price(symbol, date1, hour)
    price2 = fetch_price(symbol, date2, hour)

    # Determine the resolution based on the fetched prices
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