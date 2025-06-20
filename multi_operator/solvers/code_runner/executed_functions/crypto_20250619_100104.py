import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

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
        print(f"Proxy failed, error: {e}, trying primary endpoint.")
        # Fallback to primary endpoint
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Both endpoints failed, error: {e}")
            return None

def resolve_market():
    """
    Resolves the market based on the BTC/USDT price data from Binance.
    """
    # Define the specific time for the event
    event_time_utc = datetime(2025, 6, 19, 9, 0)  # 5 AM ET in UTC
    start_time = int(event_time_utc.timestamp() * 1000)
    end_time = int((event_time_utc + timedelta(minutes=60)).timestamp() * 1000)

    # Fetch the data
    data = fetch_binance_data("BTCUSDT", "1h", start_time, end_time)
    if data:
        open_price = float(data[1])
        close_price = float(data[4])
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50 due to data fetch failure

if __name__ == "__main__":
    result = resolve_market()
    print(result)