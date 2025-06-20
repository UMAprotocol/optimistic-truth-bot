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
        print(f"Proxy API failed: {e}, falling back to primary API")
        # Fallback to the primary API if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price data of the specified symbol at the target datetime.
    
    Args:
        symbol (str): The symbol to fetch data for (e.g., 'ETHUSDT').
        target_datetime (datetime): The datetime for which to fetch the price data.
    
    Returns:
        str: The resolution of the market ('p1', 'p2', or 'p3').
    """
    # Convert datetime to UTC and to milliseconds
    target_timestamp = int(target_datetime.timestamp() * 1000)
    
    # Fetch price data for the specified hour
    data = fetch_price_data(symbol, "1h", target_timestamp, target_timestamp + 3600000)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        
        if close_price >= open_price:
            return "p2"  # Market resolves to "Up"
        else:
            return "p1"  # Market resolves to "Down"
    else:
        return "p3"  # Market resolves to unknown/50-50 if no data is available

def main():
    # Define the target datetime for the market resolution
    target_datetime_str = "2025-06-18 10:00:00"
    timezone_str = "US/Eastern"
    symbol = "ETHUSDT"
    
    # Convert string to datetime object in the specified timezone
    timezone = pytz.timezone(timezone_str)
    target_datetime = timezone.localize(datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S"))
    
    # Resolve the market
    resolution = resolve_market(symbol, target_datetime)
    
    # Print the resolution
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()