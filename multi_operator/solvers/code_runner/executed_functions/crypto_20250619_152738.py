import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
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
        # Try fetching data using the proxy API
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy API failed, error: {e}. Trying primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary API also failed, error: {e}.")
            return None

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the opening and closing prices of the specified symbol at the target time.
    """
    # Convert target time to UTC milliseconds
    target_time_utc = int(target_time.timestamp() * 1000)

    # Fetch data for the specific minute
    data = fetch_binance_data(symbol, "1h", target_time_utc, target_time_utc + 3600000)  # 1 hour in milliseconds

    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50 if no data

def main():
    # Define the symbol and the specific time for the market resolution
    symbol = "BTCUSDT"
    target_time_str = "2025-06-19 10:00:00"
    timezone_str = "America/New_York"

    # Convert string time to datetime object in the specified timezone
    timezone = pytz.timezone(timezone_str)
    target_time = timezone.localize(datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S"))

    # Resolve the market
    result = resolve_market(symbol, target_time)
    print(result)

if __name__ == "__main__":
    main()