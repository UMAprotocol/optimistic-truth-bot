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
    Fetches price data from Binance using the proxy endpoint with a fallback to the primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the open and close prices of the specified symbol at the target datetime.
    """
    # Convert target datetime to UTC timestamp in milliseconds
    target_timestamp_utc = int(target_datetime.timestamp() * 1000)
    
    # Fetch price data for the 1 hour interval containing the target datetime
    data = fetch_price_data(symbol, "1h", target_timestamp_utc, target_timestamp_utc + 3600000)
    
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50

def main():
    # Define the symbol and the specific date and time for the market resolution
    symbol = "SOLUSDT"
    target_datetime_str = "2025-06-20 02:00:00"
    timezone_str = "US/Eastern"
    
    # Convert the target datetime string to a datetime object in the specified timezone
    timezone = pytz.timezone(timezone_str)
    target_datetime = timezone.localize(datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S"))
    
    # Convert the target datetime to UTC
    target_datetime_utc = target_datetime.astimezone(pytz.utc)
    
    # Resolve the market
    resolution = resolve_market(symbol, target_datetime_utc)
    
    # Print the resolution recommendation
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()