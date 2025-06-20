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
    Fetches the ETH/USDT price data from Binance using the specified parameters.
    Args:
        symbol (str): The symbol for the trading pair.
        interval (str): The interval for the klines data.
        start_time (int): The start time in milliseconds for the data.
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
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to the primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_date_time):
    """
    Resolves the market based on the ETH/USDT price data at the specified date and time.
    Args:
        symbol (str): The symbol for the trading pair.
        target_date_time (datetime): The target datetime object.
    Returns:
        str: The resolution of the market ('p1' for Down, 'p2' for Up, 'p3' for unknown).
    """
    # Convert target datetime to UTC timestamp in milliseconds
    target_timestamp = int(target_date_time.timestamp() * 1000)
    
    # Fetch the price data
    data = fetch_eth_price_data(symbol, "1h", target_timestamp)
    
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
    # Define the target date and time for the market resolution
    target_date_str = "2025-06-19"
    target_time_str = "09:00:00"
    timezone_str = "US/Eastern"
    
    # Convert the target time to UTC
    tz = pytz.timezone(timezone_str)
    target_date_time = datetime.strptime(f"{target_date_str} {target_time_str}", "%Y-%m-%d %H:%M:%S")
    target_date_time = tz.localize(target_date_time).astimezone(pytz.utc)
    
    # Symbol for the trading pair
    symbol = "ETHUSDT"
    
    # Resolve the market
    resolution = resolve_market(symbol, target_date_time)
    
    # Print the resolution
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()