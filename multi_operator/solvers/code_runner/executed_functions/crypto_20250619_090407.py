import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"

def fetch_price_data(symbol, start_time):
    """
    Fetches price data from Binance using a proxy endpoint with a fallback to the primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later in milliseconds
    }

    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]  # Return the first (and only) candle
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to the primary endpoint
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]  # Return the first (and only) candle
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            return None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price data fetched for the specified datetime.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)

    # Fetch the price data
    candle = fetch_price_data(symbol, start_time)
    if candle:
        open_price = float(candle[1])
        close_price = float(candle[4])
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50 due to data fetch failure

def main():
    # Example usage
    symbol = "SOLUSDT"
    target_datetime = datetime(2025, 6, 19, 4, 0)  # June 19, 2025, 4:00 AM ET
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()