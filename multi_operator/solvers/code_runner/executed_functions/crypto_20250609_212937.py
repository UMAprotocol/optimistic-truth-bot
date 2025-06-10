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

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API using a proxy with a fallback to the primary API.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
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
            return data[0]
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary API.")
        # Fallback to the primary API if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def convert_to_utc_timestamp(date_str, hour):
    """
    Converts a given date and hour to UTC timestamp.
    """
    local_time = datetime.strptime(f"{date_str} {hour}:00:00", "%Y-%m-%d %H:%M:%S")
    local_time = pytz.timezone("America/New_York").localize(local_time)
    utc_time = local_time.astimezone(pytz.utc)
    return int(utc_time.timestamp() * 1000)

def main():
    # Specific date and time for the event
    date_str = "2025-05-30"
    hour = 15  # 3 PM ET

    # Convert event time to UTC timestamp
    start_time = convert_to_utc_timestamp(date_str, hour)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch price data for the BTC/USDT pair
    price_data = fetch_price_data("BTCUSDT", start_time, end_time)
    
    if price_data:
        open_price = float(price_data[1])
        close_price = float(price_data[4])
        price_change = close_price - open_price
        
        # Determine the resolution based on price change
        if price_change >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 if data is not available

if __name__ == "__main__":
    main()