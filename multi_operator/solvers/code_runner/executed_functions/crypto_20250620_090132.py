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
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
        else:
            raise ValueError("No data returned from proxy endpoint.")
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the open and close price for a specific 1-hour candle on Binance.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch data
    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        raise Exception("Failed to retrieve data.")

def resolve_market():
    """
    Resolves the market based on the open and close prices of the BTC/USDT pair.
    """
    # Define the target datetime for the candle
    target_datetime = datetime(2025, 6, 20, 4, 0, tzinfo=pytz.timezone("US/Eastern"))

    # Get the open and close prices
    open_price, close_price = get_candle_data("BTCUSDT", target_datetime)

    # Determine the market resolution
    if close_price >= open_price:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

if __name__ == "__main__":
    try:
        result = resolve_market()
        print(result)
    except Exception as e:
        print(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 if an error occurs