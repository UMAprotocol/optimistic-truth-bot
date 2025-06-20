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

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy failed, trying primary endpoint: {e}")
        # Fallback to primary endpoint
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Both proxy and primary endpoints failed: {e}")
            return None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the open and close prices of the specified symbol at the target datetime.
    """
    # Convert target datetime to UTC milliseconds
    target_time_utc = int(target_datetime.timestamp() * 1000)

    # Fetch data for the 1 hour interval containing the target datetime
    data = fetch_binance_data(symbol, "1h", target_time_utc, target_time_utc + 3600000)  # 1 hour in milliseconds

    if data:
        open_price = float(data[1])
        close_price = float(data[4])
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    # Example: Solana on June 19, 2025, 4AM ET
    symbol = "SOLUSDT"
    target_datetime_str = "2025-06-19 04:00:00"
    timezone_str = "US/Eastern"

    # Convert to datetime object
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = pytz.timezone(timezone_str).localize(target_datetime)
    target_datetime_utc = target_datetime.astimezone(pytz.utc)

    # Resolve the market
    result = resolve_market(symbol, target_datetime_utc)
    print(result)

if __name__ == "__main__":
    main()