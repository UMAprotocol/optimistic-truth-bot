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
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_candle_data(symbol, start_time):
    """
    Fetches the open and close price for a specific 1-hour candle from Binance.
    
    Args:
        symbol (str): The symbol to fetch data for, e.g., 'SOLUSDT'.
        start_time (int): The start time of the candle in milliseconds.
    
    Returns:
        tuple: (open_price, close_price) if successful, None otherwise.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "startTime": start_time,
        "endTime": start_time + 3600000,  # 1 hour later
        "limit": 1
    }
    
    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return (open_price, close_price)
    except Exception as e:
        print(f"Proxy failed, error: {e}. Trying primary endpoint.")
        try:
            # Fallback to the primary endpoint
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                open_price = float(data[0][1])
                close_price = float(data[0][4])
                return (open_price, close_price)
        except Exception as e:
            print(f"Both proxy and primary endpoints failed, error: {e}")
            return None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the open and close prices of the specified symbol at the target datetime.
    
    Args:
        symbol (str): The trading symbol, e.g., 'SOLUSDT'.
        target_datetime (datetime): The datetime for which to fetch the candle data.
    
    Returns:
        str: 'recommendation: p1' for Down, 'recommendation: p2' for Up, 'recommendation: p4' if data fetch fails.
    """
    # Convert datetime to UTC timestamp in milliseconds
    utc_datetime = target_datetime.astimezone(pytz.utc)
    start_time_ms = int(utc_datetime.timestamp() * 1000)
    
    # Fetch candle data
    candle_data = fetch_candle_data(symbol, start_time_ms)
    if candle_data:
        open_price, close_price = candle_data
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p4"  # Unable to fetch data

def main():
    # Example usage
    symbol = "SOLUSDT"
    target_datetime = datetime(2025, 6, 17, 21, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()