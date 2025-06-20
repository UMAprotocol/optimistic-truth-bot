import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "startTime": start_time,
        "endTime": end_time
    }
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to the primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of the symbol at the specified datetime.
    """
    # Convert target datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch price data
    data = fetch_price_data(symbol, start_time, end_time)
    if not data:
        return "recommendation: p4"

    # Extract opening and closing prices
    open_price = float(data[0][1])
    close_price = float(data[0][4])

    # Determine market resolution
    if close_price >= open_price:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

def main():
    # Example usage
    symbol = "ETHUSDT"
    target_datetime = datetime(2025, 6, 17, 7, 0)  # June 17, 2025, 7:00 AM ET
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()