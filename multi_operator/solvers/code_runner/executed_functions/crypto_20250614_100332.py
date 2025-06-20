import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to the primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            return None

def get_percentage_change(data):
    """
    Calculate the percentage change from the open to close price.
    """
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        if open_price == 0:
            return None
        return ((close_price - open_price) / open_price) * 100
    return None

def main():
    # Define the parameters for the query
    symbol = "ETHUSDT"
    interval = "1h"
    target_time = datetime(2025, 6, 14, 5, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    target_time_utc = target_time.astimezone(pytz.utc)
    start_time = int(target_time_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    # Fetch the price data
    data = fetch_price_data(symbol, interval, start_time, end_time)
    
    # Calculate the percentage change
    percentage_change = get_percentage_change(data)
    
    # Determine the resolution based on the percentage change
    if percentage_change is None:
        print("recommendation: p3")  # Unknown or data fetch error
    elif percentage_change >= 0:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

if __name__ == "__main__":
    main()