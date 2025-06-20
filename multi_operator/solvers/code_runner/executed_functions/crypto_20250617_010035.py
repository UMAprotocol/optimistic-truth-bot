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

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    
    Args:
        symbol (str): The symbol to fetch data for.
        interval (str): The interval of the klines data.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        float: The closing price of the symbol at the specified time.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy API first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy API failed: {e}, falling back to primary API")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Closing price
        except Exception as e:
            print(f"Primary API failed: {e}")
            return None

def resolve_market():
    """
    Resolves the market based on the price change of ETH/USDT on Binance.
    """
    symbol = "ETHUSDT"
    interval = "1h"
    target_time = datetime(2025, 6, 16, 20, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    target_time_utc = target_time.astimezone(pytz.utc)
    start_time = int(target_time_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch closing prices at the start and end of the interval
    start_price = fetch_price_data(symbol, interval, start_time, start_time + 60000)
    end_price = fetch_price_data(symbol, interval, end_time - 60000, end_time)

    if start_price is None or end_price is None:
        print("recommendation: p4")  # Unable to fetch data
    elif end_price >= start_price:
        print("recommendation: p2")  # Price went up or stayed the same
    else:
        print("recommendation: p1")  # Price went down

if __name__ == "__main__":
    resolve_market()