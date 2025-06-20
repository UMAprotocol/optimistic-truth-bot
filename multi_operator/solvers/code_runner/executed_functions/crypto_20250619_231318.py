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
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the opening and closing prices of the candle.
    Args:
        symbol (str): The trading symbol.
        target_time (datetime): The target datetime for the candle.
    Returns:
        str: The resolution of the market.
    """
    # Convert target time to milliseconds since epoch
    start_time = int(target_time.timestamp() * 1000)
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
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    # Define the symbol and the specific time for the market
    symbol = "SOLUSDT"
    target_time_str = "2025-06-19 18:00:00"
    timezone_str = "US/Eastern"

    # Convert string to datetime
    target_time = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
    target_time = pytz.timezone(timezone_str).localize(target_time)

    # Resolve the market
    result = resolve_market(symbol, target_time)
    print(result)

if __name__ == "__main__":
    main()