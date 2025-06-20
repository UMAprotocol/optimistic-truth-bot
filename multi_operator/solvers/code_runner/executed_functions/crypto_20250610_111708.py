import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

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
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }
    
    try:
        # Try fetching data using the proxy URL first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy request failed: {e}, falling back to primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary API request also failed: {e}")
            return None

def get_price_change(symbol, target_datetime):
    """
    Determines the price change for a given cryptocurrency symbol at a specific datetime.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch data
    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return ((close_price - open_price) / open_price) * 100
    else:
        return None

def main():
    # Define the target datetime for the query
    target_datetime = datetime(2025, 6, 9, 19, 0)  # June 9, 2025, 7 PM ET

    # Get the price change percentage
    price_change = get_price_change("BTCUSDT", target_datetime)

    # Determine the resolution based on the price change
    if price_change is None:
        print("recommendation: p3")  # Unknown or data not available
    elif price_change >= 0:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

if __name__ == "__main__":
    main()