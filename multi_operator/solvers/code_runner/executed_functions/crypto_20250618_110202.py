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
        symbol (str): The symbol to fetch data for, e.g., 'SOLUSDT'.
        interval (str): The interval of the klines data, e.g., '1h'.
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
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Both proxy and primary API requests failed, error: {e}.")
            return None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price data of the specified symbol at the target datetime.
    
    Args:
        symbol (str): The symbol to check, e.g., 'SOLUSDT'.
        target_datetime (datetime): The datetime for which to check the price.
    
    Returns:
        str: The resolution of the market ('p1', 'p2', or 'p4').
    """
    # Convert target datetime to UTC and milliseconds
    target_time_utc = target_datetime.astimezone(pytz.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later in milliseconds

    # Fetch the price data
    data = fetch_price_data(symbol, "1h", start_time_ms, end_time_ms)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        
        if close_price >= open_price:
            return "p2"  # Market resolves to "Up"
        else:
            return "p1"  # Market resolves to "Down"
    else:
        return "p4"  # Unable to resolve due to data fetch failure

def main():
    # Define the symbol and the specific date and time for the market resolution
    symbol = "SOLUSDT"
    target_datetime = datetime(2025, 6, 18, 6, 0, tzinfo=pytz.timezone("US/Eastern"))
    
    # Resolve the market
    resolution = resolve_market(symbol, target_datetime)
    
    # Print the resolution recommendation
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()