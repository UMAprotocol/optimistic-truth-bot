import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz

# Load environment variables
load_dotenv()

# API keys
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
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            return None

def get_utc_timestamp(year, month, day, hour, minute, tz_name):
    """
    Converts local time to UTC timestamp.
    """
    local_tz = pytz.timezone(tz_name)
    local_time = local_tz.localize(datetime(year, month, day, hour, minute))
    utc_time = local_time.astimezone(pytz.utc)
    return int(utc_time.timestamp() * 1000)

def analyze_price_change(data):
    """
    Analyzes the price change from the fetched data.
    """
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    return "p3"  # Unknown/50-50 if no data

def main():
    # Define the parameters for the date and time of interest
    year, month, day = 2025, 6, 3
    hour, minute = 3, 0  # 3 AM ET
    tz_name = "US/Eastern"
    
    # Get the start and end timestamps for the 1-hour candle
    start_timestamp = get_utc_timestamp(year, month, day, hour, minute, tz_name)
    end_timestamp = start_timestamp + 3600000  # 1 hour later in milliseconds
    
    # Fetch the price data
    data = fetch_price_data("BTCUSDT", "1h", start_timestamp, end_timestamp)
    
    # Analyze the price change
    result = analyze_price_change(data)
    
    # Print the recommendation based on the price change
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()