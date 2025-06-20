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
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary API endpoint.")
        # Fallback to the primary API endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def convert_to_utc_timestamp(date_str, time_str, timezone_str):
    """
    Converts local time to UTC timestamp.
    """
    local_tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    local_dt = local_tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    # Specific date and time for the event
    event_date = "2025-06-13"
    event_time = "20:00:00"  # 8 PM ET
    timezone_str = "US/Eastern"
    
    # Convert event time to UTC timestamp
    start_time = convert_to_utc_timestamp(event_date, event_time, timezone_str)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch price data for BTC/USDT
    data = fetch_price_data("BTCUSDT", "1h", start_time, end_time)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = (close_price - open_price) / open_price * 100

        # Determine the resolution based on price change
        if price_change >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 if no data available

if __name__ == "__main__":
    main()