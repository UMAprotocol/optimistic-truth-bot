import requests
import os
from datetime import datetime
from pytz import timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time):
    """
    Fetches the price data for a given symbol at a specified start time using Binance API.
    Implements a fallback mechanism from proxy to primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later in milliseconds
    }
    
    try:
        # Try fetching from proxy endpoint
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]

    raise Exception("Failed to retrieve data from both endpoints.")

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price movement of the specified symbol at the target datetime.
    """
    # Convert datetime to UTC timestamp in milliseconds
    utc_datetime = target_datetime.astimezone(timezone('UTC'))
    utc_timestamp_ms = int(utc_datetime.timestamp() * 1000)

    # Fetch price data
    try:
        price_data = fetch_price_data(symbol, utc_timestamp_ms)
        open_price = float(price_data[1])
        close_price = float(price_data[4])

        # Determine market resolution
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    except Exception as e:
        print(f"Error resolving market: {e}")
        return "recommendation: p3"  # Unknown/50-50

def main():
    # Example usage
    symbol = "SOLUSDT"
    target_datetime = datetime(2025, 6, 19, 0, 0, tzinfo=timezone('US/Eastern'))
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()