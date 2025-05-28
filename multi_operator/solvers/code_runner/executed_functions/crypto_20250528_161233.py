import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price(symbol, date_str, timezone_str="US/Eastern"):
    """
    Fetches the closing price of a cryptocurrency from Binance at a specified date and time.
    """
    # Convert date string to UTC timestamp
    local_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    local_tz = pytz.timezone(timezone_str)
    local_dt = local_tz.localize(local_time)
    utc_dt = local_dt.astimezone(pytz.utc)
    timestamp = int(utc_dt.timestamp() * 1000)  # Convert to milliseconds

    # Prepare parameters for API request
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 60000  # 1 minute range
    }

    # Try fetching data from the proxy endpoint first
    try:
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])  # Closing price is the fifth element in the list
        return close_price
    except Exception as e:
        print(f"Proxy failed, error: {e}. Trying primary API.")

    # Fallback to the primary API if proxy fails
    try:
        response = requests.get(PRIMARY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        print(f"Primary API failed, error: {e}.")
        return None

def main():
    # Define the symbol and times for price checks
    symbol = "XRPUSDT"
    date1_str = "2025-05-27 12:00"
    date2_str = "2025-05-28 12:00"

    # Fetch prices
    price1 = fetch_price(symbol, date1_str)
    price2 = fetch_price(symbol, date2_str)

    # Determine the resolution based on the prices
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