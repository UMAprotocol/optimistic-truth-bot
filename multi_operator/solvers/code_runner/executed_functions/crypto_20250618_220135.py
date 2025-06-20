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
        symbol (str): The symbol to fetch data for (e.g., 'ETHUSDT').
        interval (str): The interval of the klines data (e.g., '1h').
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        dict: The JSON response containing the price data.
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
        return response.json()
    except Exception as e:
        print(f"Proxy API failed, error: {e}. Falling back to primary API.")
        # Fallback to the primary API if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_date_time):
    """
    Resolves the market based on the price movement of the specified symbol at the given date and time.
    
    Args:
        symbol (str): The trading symbol (e.g., 'ETHUSDT').
        target_date_time (datetime): The datetime object representing the target date and time.
    
    Returns:
        str: The resolution of the market ('p1', 'p2', or 'p3').
    """
    # Convert target datetime to UTC and to milliseconds
    target_time_utc = target_date_time.astimezone(pytz.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later
    
    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_time_ms, end_time_ms)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data available

def main():
    # Define the target date and time for the market resolution
    target_date_str = "2025-06-18"
    target_time_str = "17:00:00"
    timezone_str = "US/Eastern"
    
    # Convert string to datetime object
    target_date_time = datetime.strptime(f"{target_date_str} {target_time_str}", "%Y-%m-%d %H:%M:%S")
    target_date_time = pytz.timezone(timezone_str).localize(target_date_time)
    
    # Symbol for the market
    symbol = "ETHUSDT"
    
    # Resolve the market
    resolution = resolve_market(symbol, target_date_time)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()