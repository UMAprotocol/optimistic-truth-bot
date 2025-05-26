import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price(symbol, date_str, timezone_str="US/Eastern"):
    """
    Fetches the closing price of a cryptocurrency for a specific minute candle on a given date and time.
    """
    # Convert date string to datetime object in the specified timezone
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)

    # Convert datetime to milliseconds since epoch
    start_time = int(utc_datetime.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later

    # Try fetching data from the proxy API first
    try:
        response = requests.get(PROXY_API_URL, params={
            "symbol": symbol,
            "interval": "1m",
            "limit": 1,
            "startTime": start_time,
            "endTime": end_time
        }, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Proxy API failed: {e}, falling back to primary API")

    # Fallback to the primary API if proxy fails
    try:
        response = requests.get(PRIMARY_API_URL, params={
            "symbol": symbol,
            "interval": "1m",
            "limit": 1,
            "startTime": start_time,
            "endTime": end_time
        }, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Primary API failed: {e}")
        return None

def main():
    # Define the symbol and times for price comparison
    symbol = "HYPEUSDC"
    date1 = "2025-05-23 12:00"
    date2 = "2025-05-24 12:00"

    # Fetch prices
    price1 = fetch_price(symbol, date1)
    price2 = fetch_price(symbol, date2)

    # Determine the resolution based on prices
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