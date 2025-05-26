import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3/klines"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price(symbol, date_str, timezone_str="US/Eastern"):
    """
    Fetch the closing price of a cryptocurrency from Binance at a specified date and time.
    """
    # Convert date string to UTC timestamp
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    timestamp = int(utc_datetime.timestamp() * 1000)  # Convert to milliseconds

    # Prepare API request parameters
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": timestamp,
        "endTime": timestamp + 60000  # 1 minute range
    }

    # Try fetching data from the proxy endpoint first
    try:
        response = requests.get(PROXY_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])  # Closing price is the fifth element
        return close_price
    except Exception as e:
        print(f"Proxy failed, error: {e}. Trying primary endpoint.")

    # Fallback to the primary endpoint if proxy fails
    try:
        response = requests.get(PRIMARY_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        print(f"Both proxy and primary endpoint failed, error: {e}.")
        return None

def main():
    # Define the symbol and the specific times to check
    symbol = "XRPUSDT"
    date1 = "2025-05-25 12:00"
    date2 = "2025-05-26 12:00"

    # Fetch prices
    price1 = fetch_price(symbol, date1)
    price2 = fetch_price(symbol, date2)

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