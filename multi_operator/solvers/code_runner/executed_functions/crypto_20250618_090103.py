import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, start_time):
    """
    Fetches the open and close price for a specific symbol and time from Binance.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later in milliseconds
    }

    try:
        # Try proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as proxy_error:
        print(f"Proxy endpoint failed: {proxy_error}, falling back to primary endpoint")
        try:
            # Fall back to primary endpoint if proxy fails
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params)
            response.raise_for_status()
            data = response.json()
        except Exception as primary_error:
            print(f"Primary endpoint also failed: {primary_error}")
            return None

    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        return None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the open and close prices of the symbol at the target datetime.
    """
    # Convert datetime to UTC timestamp in milliseconds
    target_timestamp = int(target_datetime.timestamp() * 1000)

    # Fetch data from Binance
    result = fetch_binance_data(symbol, target_timestamp)
    if result:
        open_price, close_price = result
        if close_price >= open_price:
            return "recommendation: p2"  # Market resolves to "Up"
        else:
            return "recommendation: p1"  # Market resolves to "Down"
    else:
        return "recommendation: p3"  # Unknown/50-50 if data fetching fails

def main():
    # Define the symbol and the exact date and time for the event
    symbol = "SOLUSDT"
    target_datetime_str = "2025-06-18 04:00:00"
    timezone_str = "America/New_York"  # Eastern Time

    # Convert string to datetime object in the specified timezone
    timezone = pytz.timezone(timezone_str)
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = timezone.localize(target_datetime)

    # Resolve the market
    resolution = resolve_market(symbol, target_datetime)
    print(resolution)

if __name__ == "__main__":
    main()