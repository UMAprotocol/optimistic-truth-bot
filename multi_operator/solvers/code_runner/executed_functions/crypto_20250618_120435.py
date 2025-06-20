import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }
    try:
        # Try fetching from proxy first
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
        else:
            raise ValueError("No data returned from proxy.")
    except Exception as e:
        print(f"Proxy failed with error: {e}. Trying primary API.")
        # Fallback to primary API
        response = requests.get(PRIMARY_API_URL, params=params)
        response.raise_for_status()
        return response.json()

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the open and close price for a specific 1-hour candle.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        raise ValueError("Failed to retrieve data.")

def main():
    # Define the target date and time for the BTC/USDT pair
    target_datetime_str = "2025-06-18 07:00:00"
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = pytz.timezone("America/New_York").localize(target_datetime)

    try:
        open_price, close_price = get_candle_data("BTCUSDT", target_datetime)
        print(f"Open Price: {open_price}, Close Price: {close_price}")

        # Determine the market resolution based on the open and close prices
        if close_price >= open_price:
            print("recommendation: p2")  # Market resolves to "Up"
        else:
            print("recommendation: p1")  # Market resolves to "Down"
    except Exception as e:
        print(f"An error occurred: {e}")
        print("recommendation: p3")  # Unable to determine, resolve as unknown/50-50

if __name__ == "__main__":
    main()