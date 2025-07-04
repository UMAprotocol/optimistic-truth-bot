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

def resolve_market(symbol, target_date_time):
    """
    Resolves the market based on the price change of the symbol at the specified date and time.
    """
    # Convert target datetime to UTC timestamp in milliseconds
    target_time_utc = int(target_date_time.timestamp() * 1000)

    # Fetch data for the specified time
    data = fetch_binance_data(symbol, "1h", target_time_utc, target_time_utc + 3600000)  # 1 hour in ms

    if data:
        open_price = float(data[1])
        close_price = float(data[4])
        price_change = (close_price - open_price) / open_price * 100

        if price_change >= 0:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    # Define the target date and time for the market resolution
    target_date_str = "2025-06-07"
    target_time_str = "05:00:00"
    timezone_str = "US/Eastern"

    # Convert to datetime object
    target_date_time = datetime.strptime(f"{target_date_str} {target_time_str}", "%Y-%m-%d %H:%M:%S")
    target_date_time = pytz.timezone(timezone_str).localize(target_date_time)

    # Convert to UTC
    target_date_time = target_date_time.astimezone(pytz.utc)

    # Symbol for the market
    symbol = "BTCUSDT"

    # Resolve the market
    result = resolve_market(symbol, target_date_time)
    print(result)

if __name__ == "__main__":
    main()