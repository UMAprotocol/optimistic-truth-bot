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
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of a cryptocurrency pair.
    
    Args:
        symbol (str): The trading pair symbol (e.g., 'ETHUSDT').
        target_datetime (datetime): The datetime for which the price change is to be evaluated.
    
    Returns:
        str: The resolution of the market ('p1' for Down, 'p2' for Up, 'p3' for unknown).
    """
    # Convert target datetime to UTC and milliseconds
    target_time_utc = target_datetime.astimezone(pytz.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later
    
    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_time_ms, end_time_ms)
    
    if not data or 'data' not in data or len(data['data']) == 0:
        return "p3"  # Unknown or no data available
    
    # Extract the opening and closing prices
    open_price = float(data['data'][0][1])
    close_price = float(data['data'][0][4])
    
    # Determine if the price went up or down
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    # Example date and time for the market resolution
    target_datetime_str = "2025-06-17 10:00:00"
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = pytz.timezone("America/New_York").localize(target_datetime)
    
    # Symbol for the market
    symbol = "ETHUSDT"
    
    # Resolve the market
    resolution = resolve_market(symbol, target_datetime)
    
    # Print the resolution
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()