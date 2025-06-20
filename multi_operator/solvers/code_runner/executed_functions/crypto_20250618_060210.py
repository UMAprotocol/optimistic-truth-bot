import requests
import os
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_data_from_binance(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance using the proxy endpoint with a fallback to the primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
        else:
            raise ValueError("No data returned from proxy endpoint.")
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_eth_price_data(event_time):
    """
    Retrieves the open and close price for the ETH/USDT pair for the specified event time.
    """
    # Convert event time to UTC timestamp in milliseconds
    event_time_utc = event_time.astimezone(timezone.utc)
    start_time_ms = int(event_time_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later in milliseconds

    # Fetch data
    data = fetch_data_from_binance("ETHUSDT", "1h", start_time_ms, end_time_ms)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        raise Exception("Failed to retrieve data.")

def main():
    # Define the event time in Eastern Time
    event_time_str = "2025-06-18 01:00:00"
    event_time = datetime.strptime(event_time_str, "%Y-%m-%d %H:%M:%S")
    event_time = pytz.timezone("US/Eastern").localize(event_time)

    try:
        open_price, close_price = get_eth_price_data(event_time)
        print(f"Open Price: {open_price}, Close Price: {close_price}")
        if close_price >= open_price:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        print(f"Error: {e}")
        print("recommendation: p3")  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    main()