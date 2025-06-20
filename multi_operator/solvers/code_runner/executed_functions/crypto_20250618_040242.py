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

def fetch_candle_data(symbol, interval, start_time, end_time):
    """
    Fetches candle data for a given symbol and interval from Binance API.
    Args:
        symbol (str): The symbol to fetch data for.
        interval (str): The interval of the candle data.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    Returns:
        dict: The candle data.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }
    try:
        # Try fetching data from the proxy API first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy API failed, trying primary API: {e}")
        # Fallback to the primary API if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the opening and closing prices of a candle.
    Args:
        symbol (str): The trading symbol.
        target_datetime (datetime): The datetime for which to fetch the candle.
    Returns:
        str: The resolution of the market.
    """
    # Convert target datetime to UTC and to milliseconds
    target_datetime_utc = target_datetime.astimezone(pytz.utc)
    start_time = int(target_datetime_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch candle data
    candle = fetch_candle_data(symbol, "1h", start_time, end_time)
    if candle:
        open_price = float(candle[1])
        close_price = float(candle[4])
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    return "recommendation: p3"  # Unknown/50-50 if no data

def main():
    # Define the symbol and the specific date and time
    symbol = "SOLUSDT"
    target_datetime = datetime(2025, 6, 17, 23, 0, tzinfo=pytz.timezone("US/Eastern"))

    # Resolve the market
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()