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
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to the primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            return None

def get_utc_timestamp(year, month, day, hour, minute, tz_name):
    """
    Converts local time to UTC timestamp.
    """
    local_tz = pytz.timezone(tz_name)
    local_time = local_tz.localize(datetime(year, month, day, hour, minute, 0))
    utc_time = local_time.astimezone(pytz.utc)
    return int(utc_time.timestamp() * 1000)

def main():
    # Specific date and time for the event
    year, month, day = 2025, 6, 11
    hour, minute = 6, 0  # 6 AM ET
    tz_name = "US/Eastern"
    
    # Get the start and end timestamps in UTC
    start_timestamp = get_utc_timestamp(year, month, day, hour, minute, tz_name)
    end_timestamp = start_timestamp + 3600000  # 1 hour later
    
    # Fetch the price data for BTCUSDT
    data = fetch_price_data("BTCUSDT", "1h", start_timestamp, end_timestamp)
    
    if data:
        open_price = float(data[1])
        close_price = float(data[4])
        price_change_percentage = ((close_price - open_price) / open_price) * 100
        
        # Determine the resolution based on the price change
        if price_change_percentage >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data fetch failure

if __name__ == "__main__":
    main()