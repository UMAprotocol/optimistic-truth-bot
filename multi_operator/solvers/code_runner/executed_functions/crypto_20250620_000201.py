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
    Fetches price data from Binance API with a fallback to a proxy server.
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
        print(f"Proxy failed with error: {e}, trying primary API.")
        # Fallback to the primary API endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_date):
    """
    Resolves the market based on the price data of the symbol on the target date.
    """
    # Convert target date to the start and end timestamps for the 1-hour candle
    start_dt = datetime.strptime(target_date, "%Y-%m-%d %H:%M:%S")
    start_timestamp = int(start_dt.timestamp() * 1000)  # Convert to milliseconds
    end_timestamp = start_timestamp + 3600000  # Add one hour in milliseconds

    # Fetch price data
    price_data = fetch_price_data(symbol, start_timestamp, end_timestamp)
    
    if not price_data or len(price_data) == 0:
        return "recommendation: p4"  # Unable to resolve due to lack of data

    # Extract open and close prices
    open_price = float(price_data[0][1])
    close_price = float(price_data[0][4])

    # Determine the market resolution
    if close_price >= open_price:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

def main():
    # Example usage
    symbol = "SOLUSDT"
    target_date = "2025-06-19 19:00:00"  # June 19, 2025, 7:00 PM ET
    result = resolve_market(symbol, target_date)
    print(result)

if __name__ == "__main__":
    main()