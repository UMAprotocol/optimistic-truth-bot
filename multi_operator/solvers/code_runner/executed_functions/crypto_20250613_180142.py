import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API = "https://api.binance.com/api/v3"
PROXY_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

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
        # Try fetching from proxy API first
        response = requests.get(f"{PROXY_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy API failed: {e}, falling back to primary API.")
        try:
            # Fallback to primary API
            response = requests.get(f"{PRIMARY_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Primary API also failed: {e}")
            return None

def get_candle_data(symbol, target_datetime):
    """
    Converts the target datetime to UTC and fetches the 1-hour candle data for that time.
    """
    # Convert datetime to milliseconds
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    # Fetch the candle data
    candle_data = fetch_price_data(symbol, "1h", start_time, end_time)
    return candle_data

def main():
    # Define the target date and time
    target_datetime_str = "2025-06-13 13:00:00"
    target_timezone = "US/Eastern"
    symbol = "BTCUSDT"

    # Convert string to datetime
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = pytz.timezone(target_timezone).localize(target_datetime)
    target_datetime_utc = target_datetime.astimezone(pytz.utc)

    # Get the candle data
    candle_data = get_candle_data(symbol, target_datetime_utc)
    if candle_data:
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])
        price_change = close_price - open_price

        # Determine the resolution based on price change
        if price_change >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data fetch failure

if __name__ == "__main__":
    main()