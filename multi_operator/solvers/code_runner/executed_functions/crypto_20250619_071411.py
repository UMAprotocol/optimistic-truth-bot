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

def fetch_candle_data(symbol, interval, start_time):
    """
    Fetches candle data for a given symbol and interval from Binance API.
    Args:
        symbol (str): The symbol to fetch data for, e.g., 'SOLUSDT'.
        interval (str): The interval of the candle, e.g., '1h'.
        start_time (int): The start time for the candle data in milliseconds.
    Returns:
        dict: The candle data or None if an error occurs.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }
    try:
        # Try fetching from the proxy API first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]  # Return the first (and only) candle
    except Exception as e:
        print(f"Proxy API failed, trying primary API: {e}")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]  # Return the first (and only) candle
        except Exception as e:
            print(f"Primary API also failed: {e}")
            return None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the opening and closing prices of a candle.
    Args:
        symbol (str): The trading symbol, e.g., 'SOLUSDT'.
        target_datetime (datetime): The datetime object representing the target time.
    Returns:
        str: The resolution of the market ('p1', 'p2', or 'p3').
    """
    # Convert target datetime to UTC timestamp in milliseconds
    target_timestamp = int(target_datetime.timestamp() * 1000)
    
    # Fetch the candle data
    candle_data = fetch_candle_data(symbol, "1h", target_timestamp)
    
    if candle_data:
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])
        
        if close_price >= open_price:
            return "p2"  # Market resolves to "Up"
        else:
            return "p1"  # Market resolves to "Down"
    else:
        return "p3"  # Market resolves to unknown/50-50 if data is not available

def main():
    # Define the target date and time
    target_datetime_str = "2025-06-19 02:00:00"
    timezone_str = "US/Eastern"
    
    # Convert string to datetime object in the specified timezone
    timezone = pytz.timezone(timezone_str)
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = timezone.localize(target_datetime)
    
    # Convert to UTC
    target_datetime_utc = target_datetime.astimezone(pytz.utc)
    
    # Symbol for the market
    symbol = "SOLUSDT"
    
    # Resolve the market
    resolution = resolve_market(symbol, target_datetime_utc)
    
    # Print the resolution
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()