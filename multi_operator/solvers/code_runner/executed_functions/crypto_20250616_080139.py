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

def fetch_price_data(symbol, start_time):
    """
    Fetches price data for a given symbol at a specified start time using Binance API.
    Implements a fallback from proxy to primary endpoint.
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
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0][4]  # Close price of the candle
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to primary endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0][4]  # Close price of the candle
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            return None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of the symbol at the specified datetime.
    """
    # Convert datetime to UTC timestamp in milliseconds
    target_timestamp = int(target_datetime.timestamp() * 1000)

    # Fetch the closing price at the target datetime
    closing_price_start = fetch_price_data(symbol, target_timestamp)
    closing_price_end = fetch_price_data(symbol, target_timestamp + 3600000)

    if closing_price_start and closing_price_end:
        # Calculate the percentage change
        change = ((float(closing_price_end) - float(closing_price_start)) / float(closing_price_start)) * 100
        if change >= 0:
            return "recommendation: p2"  # Market resolves to "Up"
        else:
            return "recommendation: p1"  # Market resolves to "Down"
    else:
        return "recommendation: p3"  # Unknown or data fetch error

def main():
    # Example usage
    symbol = "ETHUSDT"
    target_datetime = datetime(2025, 6, 16, 3, 0)  # June 16, 2025, 3:00 AM ET
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()