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
    Fetches price data from Binance API with a fallback to a proxy endpoint.
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
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_date):
    """
    Resolves the market based on the opening and closing prices of the specified symbol on the target date.
    """
    # Convert target date to the beginning of the hour in UTC
    tz = pytz.timezone("US/Eastern")
    target_datetime = datetime.strptime(target_date, "%Y-%m-%d %H:%M")
    target_datetime = tz.localize(target_datetime).astimezone(pytz.utc)
    
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds
    
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
        return "p3"  # Market resolves to unknown/50-50 if no data

def main():
    # Example usage
    symbol = "ETHUSDT"
    target_date = "2025-06-20 00:00"
    resolution = resolve_market(symbol, target_date)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()