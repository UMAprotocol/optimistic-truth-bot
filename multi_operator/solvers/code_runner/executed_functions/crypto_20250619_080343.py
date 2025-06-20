import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary request fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try fetching data using the proxy URL first
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy request failed, trying primary API. Error: {e}")

    try:
        # Fallback to the primary API if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Both proxy and primary API requests failed. Error: {e}")
        return None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the opening and closing prices of the specified symbol at the target datetime.
    """
    # Convert target datetime to UTC timestamp in milliseconds
    target_timestamp_utc = int(target_datetime.timestamp() * 1000)

    # Fetch data for the 1 hour interval containing the target datetime
    data = fetch_binance_data(symbol, "1h", target_timestamp_utc, target_timestamp_utc + 3600000)

    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])

        if close_price >= open_price:
            return "recommendation: p2"  # Market resolves to "Up"
        else:
            return "recommendation: p1"  # Market resolves to "Down"
    else:
        return "recommendation: p3"  # Unknown/50-50 if no data available

def main():
    # Define the symbol and the specific datetime for the market resolution
    symbol = "BTCUSDT"
    target_datetime_str = "2025-06-19 03:00:00"
    timezone_str = "US/Eastern"

    # Convert string to datetime object in the specified timezone
    timezone = pytz.timezone(timezone_str)
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = timezone.localize(target_datetime)

    # Resolve the market
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()