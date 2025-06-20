import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_data_from_binance(symbol, interval, start_time, end_time):
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
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def get_percentage_change(data):
    """
    Calculate the percentage change from open to close price in the given data.
    """
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        if open_price == 0:
            return None
        return ((close_price - open_price) / open_price) * 100
    return None

def main():
    # Define the symbol and interval
    symbol = "BTCUSDT"
    interval = "1h"
    
    # Define the specific time for the event
    event_time = datetime(2025, 6, 11, 15, 0)  # June 11, 2025, 3 PM ET
    # Convert to UTC and milliseconds
    event_time_utc = event_time - timedelta(hours=4)  # ET is UTC-4
    start_time = int(event_time_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds
    
    # Fetch data
    data = fetch_data_from_binance(symbol, interval, start_time, end_time)
    
    # Calculate percentage change
    percentage_change = get_percentage_change(data)
    
    # Determine resolution based on percentage change
    if percentage_change is not None:
        if percentage_change >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50

if __name__ == "__main__":
    main()