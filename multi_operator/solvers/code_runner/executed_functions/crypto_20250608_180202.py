import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

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
    
    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            raise

def calculate_percentage_change(open_price, close_price):
    """
    Calculates the percentage change between the open and close prices.
    """
    return ((close_price - open_price) / open_price) * 100

def main():
    # Define the specific event details
    symbol = "BTCUSDT"
    interval = "1h"
    event_date = datetime(2025, 6, 8, 13, 0, 0)  # June 8, 2025, 1 PM ET
    timezone_et = pytz.timezone("US/Eastern")
    event_date_utc = timezone_et.localize(event_date).astimezone(pytz.utc)

    # Convert datetime to milliseconds since epoch
    start_time = int(event_date_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch data from Binance
    try:
        data = fetch_binance_data(symbol, interval, start_time, end_time)
        open_price = float(data[1])
        close_price = float(data[4])
        
        # Calculate percentage change
        change = calculate_percentage_change(open_price, close_price)
        
        # Determine resolution based on the change
        if change >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        print(f"Failed to fetch or process data: {str(e)}")
        print("recommendation: p3")  # Unknown/50-50 if data fetching fails

if __name__ == "__main__":
    main()