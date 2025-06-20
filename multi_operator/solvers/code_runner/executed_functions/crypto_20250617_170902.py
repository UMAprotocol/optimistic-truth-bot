import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz

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
        "endTime": start_time + 3600000  # 1 hour later
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

    raise Exception("Failed to fetch data from both endpoints.")

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price data of the symbol at the target datetime.
    """
    # Convert datetime to milliseconds since epoch
    target_timestamp = int(target_datetime.timestamp() * 1000)

    # Fetch price data
    try:
        price_data = fetch_price_data(symbol, target_timestamp)
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
    # Define the symbol and target datetime
    symbol = "SOLUSDT"
    target_datetime_str = "2025-06-17 12:00:00"
    timezone_str = "US/Eastern"

    # Convert string to datetime object in the specified timezone
    timezone = pytz.timezone(timezone_str)
    target_datetime = timezone.localize(datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S"))

    # Resolve the market
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()