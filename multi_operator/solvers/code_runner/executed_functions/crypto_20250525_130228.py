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
    local_dt = tz.localize(datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S"))
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

    # Try fetching data from the proxy endpoint first
    try:
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])  # Closing price is the 5th element
        return close_price
    except Exception as e:
        print(f"Proxy failed, error: {e}. Trying primary API.")

    # Fallback to the primary API if proxy fails
    try:
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])  # Closing price is the 5th element
        return close_price
    except Exception as e:
        print(f"Primary API failed, error: {e}.")
        raise

def main():
    # Define the symbols and dates based on the specific market question
    symbol = "XRPUSDT"
    date1 = "2025-05-23"
    date2 = "2025-05-24"

    # Fetch prices
    try:
        price1 = fetch_price(symbol, date1)
        price2 = fetch_price(symbol, date2)

        # Determine the resolution based on the prices
        if price1 < price2:
            print("recommendation: p2")  # Up
        elif price1 > price2:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        print(f"Failed to fetch prices or determine resolution, error: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()