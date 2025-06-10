import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

def fetch_price_from_proxy(symbol, start_time, end_time):
    """ Fetch price using the proxy endpoint """
    try:
        response = requests.get(
            f"{PROXY_URL}/klines",
            params={
                "symbol": symbol,
                "interval": "1m",
                "limit": 1,
                "startTime": start_time,
                "endTime": end_time
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return float(data[0][2])  # High price of the candle
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        return None

def fetch_price_from_primary(symbol, start_time, end_time):
    """ Fetch price using the primary endpoint """
    try:
        response = requests.get(
            f"{PRIMARY_URL}/klines",
            params={
                "symbol": symbol,
                "interval": "1m",
                "limit": 1,
                "startTime": start_time,
                "endTime": end_time
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return float(data[0][2])  # High price of the candle
    except Exception as e:
        print(f"Primary endpoint failed: {str(e)}")
        return None

def get_data(symbol, start_time, end_time):
    """ Attempt to fetch data from proxy, then fall back to primary if necessary """
    price = fetch_price_from_proxy(symbol, start_time, end_time)
    if price is None:
        price = fetch_price_from_primary(symbol, start_time, end_time)
    return price

def main():
    # Define the symbol and the time range
    symbol = "FARTCOINUSDT"
    start_time = int(datetime(2025, 4, 23, 10, 0, tzinfo=pytz.timezone("US/Eastern")).timestamp() * 1000)
    end_time = int(datetime(2025, 4, 30, 23, 59, tzinfo=pytz.timezone("US/Eastern")).timestamp() * 1000)

    # Fetch the highest price in the given time range
    highest_price = get_data(symbol, start_time, end_time)

    # Determine the resolution based on the highest price
    if highest_price is not None and highest_price >= 1.50:
        print("recommendation: p2")  # Yes
    else:
        print("recommendation: p1")  # No

if __name__ == "__main__":
    main()