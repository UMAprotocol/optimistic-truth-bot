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
        if data:
            return data[0][4]  # Close price of the candle
    except Exception as e:
        print(f"Proxy failed with error: {e}, falling back to primary endpoint.")
        # Fallback to the primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0][4]  # Close price of the candle
        except Exception as e:
            print(f"Primary endpoint also failed with error: {e}")
            return None

def convert_to_utc_timestamp(date_str, hour, minute, timezone_str):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {hour}:{minute}", "%Y-%m-%d %H:%M")
    local_dt = tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    # Specific date and time for the event
    date_str = "2025-06-05"
    hour = 6  # 6 AM ET
    minute = 0
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"
    interval = "1h"
    
    # Convert event time to UTC timestamp
    start_time = convert_to_utc_timestamp(date_str, hour, minute, timezone_str)
    end_time = start_time + 3600000  # Plus one hour in milliseconds
    
    # Fetch the closing price of the 1-hour candle starting at 6 AM ET
    close_price_start = fetch_price_data(symbol, interval, start_time, start_time)
    close_price_end = fetch_price_data(symbol, interval, end_time, end_time)
    
    if close_price_start and close_price_end:
        # Calculate the percentage change
        change_percentage = ((float(close_price_end) - float(close_price_start)) / float(close_price_start)) * 100
        # Determine the resolution based on the change
        if change_percentage >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 if data fetching failed

if __name__ == "__main__":
    main()