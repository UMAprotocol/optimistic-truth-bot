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
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to the primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of the symbol at the specified datetime.
    """
    # Convert target datetime to the appropriate timestamp for the API
    start_timestamp = int(target_datetime.timestamp() * 1000)
    end_timestamp = start_timestamp + 3600000  # 1 hour later

    # Fetch price data
    data = fetch_price_data(symbol, start_timestamp, end_timestamp)
    
    if not data or len(data) < 1:
        print("recommendation: p4")
        return

    # Extract the opening and closing prices from the first returned candle
    open_price = float(data[0][1])
    close_price = float(data[0][4])

    # Determine market resolution based on price change
    if close_price >= open_price:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

def main():
    # Example usage
    symbol = "ETHUSDT"
    target_datetime = datetime(2025, 6, 11, 9, 0)  # June 11, 2025, 9:00 AM ET
    resolve_market(symbol, target_datetime)

if __name__ == "__main__":
    main()