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

def fetch_eth_price_data(symbol, interval, start_time):
    """
    Fetches Ethereum price data from Binance using the specified parameters.
    Args:
        symbol (str): The symbol for the trading pair.
        interval (str): The interval for the candlestick data.
        start_time (int): The start time for the data in milliseconds.
    Returns:
        dict: The JSON response containing the price data.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }
    
    try:
        # Try fetching data from the proxy endpoint
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
    Resolves the market based on the Ethereum price data at the specified datetime.
    Args:
        symbol (str): The symbol for the trading pair.
        target_datetime (datetime): The datetime for which to fetch the price data.
    Returns:
        str: The resolution of the market ('p1' for Down, 'p2' for Up, 'p3' for unknown).
    """
    # Convert datetime to UTC timestamp in milliseconds
    utc_datetime = target_datetime.astimezone(pytz.utc)
    start_time_ms = int(utc_datetime.timestamp() * 1000)
    
    # Fetch price data
    data = fetch_eth_price_data(symbol, "1h", start_time_ms)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown

def main():
    # Define the target datetime for the ETH/USDT market resolution
    target_datetime = datetime(2025, 6, 18, 4, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "ETHUSDT"
    
    # Resolve the market
    resolution = resolve_market(symbol, target_datetime)
    
    # Print the resolution recommendation
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()