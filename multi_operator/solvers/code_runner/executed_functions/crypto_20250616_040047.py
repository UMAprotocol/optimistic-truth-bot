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
        symbol (str): The symbol to fetch data for, e.g., 'BTCUSDT'.
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
        print(f"Proxy API failed: {e}, falling back to primary API")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Primary API also failed: {e}")
            raise

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of a cryptocurrency at a specific datetime.
    
    Args:
        symbol (str): The cryptocurrency symbol, e.g., 'BTCUSDT'.
        target_datetime (datetime): The datetime for which to fetch the price data.
    
    Returns:
        str: The resolution of the market ('p1', 'p2', or 'p3').
    """
    # Convert target datetime to UTC and milliseconds
    target_datetime_utc = target_datetime.astimezone(pytz.utc)
    start_time = int(target_datetime_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later
    
    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    
    if not data or len(data) == 0 or len(data[0]) < 5:
        return "p3"  # Unknown or insufficient data
    
    open_price = float(data[0][1])
    close_price = float(data[0][4])
    
    # Determine if the price went up or down
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    # Example: Resolve the market for BTC/USDT on June 15, 2025, 11 PM ET
    target_datetime = datetime(2025, 6, 15, 23, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "BTCUSDT"
    
    try:
        resolution = resolve_market(symbol, target_datetime)
        print(f"recommendation: {resolution}")
    except Exception as e:
        print(f"Error resolving market: {e}")
        print("recommendation: p3")  # Default to unknown if there's an error

if __name__ == "__main__":
    main()