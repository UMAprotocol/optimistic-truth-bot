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
PRIMARY_API_URL = "https://api.binance.com/api/v3"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_candle_data(symbol, interval, start_time):
    """
    Fetches candle data for a given symbol and interval from Binance API.
    Implements a fallback from proxy to primary endpoint.
    
    Args:
        symbol (str): The symbol to fetch data for, e.g., 'SOLUSDT'.
        interval (str): The interval of the candle, e.g., '1h'.
        start_time (int): The start time for the candle data in milliseconds.
    
    Returns:
        dict: The candle data.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }
    
    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]  # Return the first (and only) candle
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to the primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_API_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]  # Return the first (and only) candle
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            raise

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the opening and closing prices of a candle.
    
    Args:
        symbol (str): The trading symbol, e.g., 'SOLUSDT'.
        target_datetime (datetime): The datetime object representing the target time.
    
    Returns:
        str: 'p1' if the market resolves to Down, 'p2' if Up, 'p3' if unknown.
    """
    # Convert target datetime to UTC timestamp in milliseconds
    utc_datetime = target_datetime.astimezone(pytz.utc)
    start_time_ms = int(utc_datetime.timestamp() * 1000)
    
    # Fetch the candle data
    candle = fetch_candle_data(symbol, "1h", start_time_ms)
    
    # Extract open and close prices
    open_price = float(candle[1])
    close_price = float(candle[4])
    
    # Determine resolution based on open and close prices
    if close_price >= open_price:
        return "p2"  # Market resolves to Up
    else:
        return "p1"  # Market resolves to Down

def main():
    # Define the target date and time
    target_datetime = datetime(2025, 6, 17, 23, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "SOLUSDT"
    
    try:
        resolution = resolve_market(symbol, target_datetime)
        print(f"recommendation: {resolution}")
    except Exception as e:
        print(f"Failed to resolve market: {e}")
        print("recommendation: p3")  # Resolve as unknown if there's an error

if __name__ == "__main__":
    main()