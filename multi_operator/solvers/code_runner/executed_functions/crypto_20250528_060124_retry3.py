import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy failed, trying primary endpoint: {e}")
        # Fallback to primary endpoint
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Both endpoints failed: {e}")
            return None

def get_candle_data(symbol, date_str, hour):
    """
    Retrieves the closing price of a specific hourly candle.
    """
    # Convert date and hour to the correct timestamp
    dt = datetime.strptime(date_str + f" {hour}:00:00", "%Y-%m-%d %H:%M:%S")
    dt = pytz.timezone("America/New_York").localize(dt)
    dt_utc = dt.astimezone(pytz.utc)

    start_time = int(dt_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour in milliseconds

    # Fetch the candle data
    candle = fetch_binance_data(symbol, "1h", start_time, end_time)
    if candle:
        return float(candle[4])  # Closing price
    return None

def main():
    symbol = "BTCUSDT"
    date_str = "2025-05-28"
    hour = 1  # 1 AM ET

    closing_price_start = get_candle_data(symbol, date_str, hour)
    if closing_price_start is None:
        print("recommendation: p4")
        return

    # Assuming the market needs to compare with the previous close
    closing_price_end = get_candle_data(symbol, date_str, hour - 1)
    if closing_price_end is None:
        print("recommendation: p4")
        return

    # Determine the resolution based on the price change
    if closing_price_start >= closing_price_end:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

if __name__ == "__main__":
    main()