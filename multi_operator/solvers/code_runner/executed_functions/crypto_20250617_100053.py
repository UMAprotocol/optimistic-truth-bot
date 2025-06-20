import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_candle_data(symbol, start_time):
    """
    Fetches the candle data for a given symbol and start time using Binance API.
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
        # Try fetching from proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]  # Return the first (and only) candle
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to primary endpoint
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]  # Return the first (and only) candle
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            return None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the opening and closing prices of the candle.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    
    # Fetch candle data
    candle = fetch_candle_data(symbol, start_time)
    
    if candle:
        open_price = float(candle[1])
        close_price = float(candle[4])
        
        if close_price >= open_price:
            return "recommendation: p2"  # Market resolves to "Up"
        else:
            return "recommendation: p1"  # Market resolves to "Down"
    else:
        return "recommendation: p3"  # Unknown/50-50 if data is not available

def main():
    # Example usage
    symbol = "SOLUSDT"
    target_datetime = datetime(2025, 6, 17, 5, 0)  # June 17, 2025, 5:00 AM ET
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()