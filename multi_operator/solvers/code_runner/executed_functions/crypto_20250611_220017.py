import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

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
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Primary API also failed: {e}")
            return None

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the symbol at the specified target time.
    
    Args:
        symbol (str): The trading symbol (e.g., 'ETHUSDT').
        target_time (datetime): The target datetime object.
    
    Returns:
        str: The resolution of the market ('p1', 'p2', or 'p3').
    """
    # Convert target time to milliseconds since epoch
    start_time = int(target_time.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later
    
    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        
        if close_price >= open_price:
            return "p2"  # Market resolves to "Up"
        else:
            return "p1"  # Market resolves to "Down"
    else:
        return "p3"  # Unknown/50-50 if no data available

def main():
    # Define the symbol and the specific time for the market resolution
    symbol = "ETHUSDT"
    target_time = datetime(2025, 6, 11, 17, 0)  # June 11, 2025, 5PM ET
    
    # Resolve the market
    resolution = resolve_market(symbol, target_time)
    
    # Print the recommendation
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()