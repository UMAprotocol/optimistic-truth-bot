import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"

def fetch_price_data(symbol, start_time):
    """
    Fetches the price data for a given symbol and start time using Binance API.
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
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fallback to primary endpoint
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price data of the symbol at the specified datetime.
    """
    # Convert datetime to milliseconds since epoch
    target_timestamp = int(target_datetime.timestamp() * 1000)
    
    # Fetch price data
    price_data = fetch_price_data(symbol, target_timestamp)
    
    if price_data:
        open_price = float(price_data[1])
        close_price = float(price_data[4])
        
        # Determine market resolution
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50 due to data fetch failure

def main():
    # Example usage
    symbol = "SOLUSDT"
    target_datetime = datetime(2025, 6, 18, 10, 0)  # June 18, 2025, 10:00 AM ET
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()