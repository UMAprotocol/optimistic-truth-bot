import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

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
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price movement of the specified symbol at the given datetime.
    """
    # Convert datetime to the appropriate timestamp for the API
    utc_datetime = target_datetime.astimezone(pytz.utc)
    start_timestamp = int(utc_datetime.timestamp() * 1000)  # Convert to milliseconds
    end_timestamp = start_timestamp + 3600000  # 1 hour later

    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_timestamp, end_timestamp)

    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        
        if close_price >= open_price:
            return "p2"  # Market resolves to "Up"
        else:
            return "p1"  # Market resolves to "Down"
    else:
        return "p3"  # Unknown/50-50 if no data is available

def main():
    # Define the target datetime and symbol
    target_datetime = datetime(2025, 6, 17, 7, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "SOLUSDT"

    # Resolve the market
    result = resolve_market(symbol, target_datetime)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()