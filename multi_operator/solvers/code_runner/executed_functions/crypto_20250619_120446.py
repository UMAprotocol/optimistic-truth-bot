import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
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
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the opening and closing prices of the specified symbol at the target time.
    """
    # Convert target time to UTC milliseconds
    utc_time = int(target_time.timestamp() * 1000)

    # Fetch price data for the 1-hour interval containing the target time
    data = fetch_price_data(symbol, "1h", utc_time, utc_time + 3600000)  # 1 hour in milliseconds

    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])

        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data available

def main():
    # Define the symbol and the specific time for the market resolution
    symbol = "SOLUSDT"
    target_time_str = "2025-06-19 07:00:00"
    timezone_str = "US/Eastern"

    # Convert the target time to a datetime object in the specified timezone
    tz = pytz.timezone(timezone_str)
    target_time = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
    target_time = tz.localize(target_time)

    # Resolve the market
    resolution = resolve_market(symbol, target_time)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()