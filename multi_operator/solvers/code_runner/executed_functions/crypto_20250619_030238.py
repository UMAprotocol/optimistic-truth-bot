import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_candle_data(symbol, interval, start_time):
    """
    Fetches candle data for a given symbol and interval from Binance API.
    Args:
        symbol (str): The symbol to fetch data for (e.g., 'SOLUSDT').
        interval (str): The interval of the candle (e.g., '1h').
        start_time (int): The start time for the candle data in milliseconds.
    Returns:
        dict: The candle data.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }
    try:
        # Try fetching from the proxy API first
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]  # Return the first (and only) candle
    except Exception as e:
        print(f"Proxy API failed, trying primary API: {e}")
        # Fallback to the primary API if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]  # Return the first (and only) candle
        except Exception as e:
            print(f"Both API requests failed: {e}")
            return None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the opening and closing prices of a candle.
    Args:
        symbol (str): The trading symbol (e.g., 'SOLUSDT').
        target_datetime (datetime): The datetime for which to fetch the candle.
    Returns:
        str: The resolution of the market ('p1', 'p2', or 'p3').
    """
    # Convert target datetime to UTC timestamp in milliseconds
    utc_datetime = target_datetime.astimezone(pytz.utc)
    start_time_ms = int(utc_datetime.timestamp() * 1000)

    # Fetch the candle data
    candle = fetch_candle_data(symbol, "1h", start_time_ms)
    if candle:
        open_price = float(candle[1])
        close_price = float(candle[4])
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data is available

def main():
    # Define the target datetime for the SOL/USDT market resolution
    target_datetime = datetime(2025, 6, 18, 22, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "SOLUSDT"
    resolution = resolve_market(symbol, target_datetime)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()