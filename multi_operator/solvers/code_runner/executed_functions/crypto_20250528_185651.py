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
    Fetches price data from Binance using the proxy endpoint with a fallback to the primary endpoint.
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
            return data[0]
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to the primary endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            raise

def get_candle_data(symbol, date_str, hour):
    """
    Retrieves the closing price for a specific hour candle on a given date for the specified symbol.
    """
    # Convert date and hour to the correct timestamp
    date = datetime.strptime(date_str, "%Y-%m-%d")
    date = date.replace(hour=hour, minute=0, second=0, microsecond=0)
    tz = pytz.timezone("America/New_York")
    date = tz.localize(date)
    start_time = int(date.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour in milliseconds

    # Fetch the candle data
    candle = fetch_price_data(symbol, "1h", start_time, end_time)
    if candle:
        open_price = float(candle[1])
        close_price = float(candle[4])
        return open_price, close_price

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the opening and closing prices.
    """
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to resolve the market for the Bitcoin price on a specific date and hour.
    """
    symbol = "BTCUSDT"
    date_str = "2025-05-28"
    hour = 11  # 11 AM ET

    try:
        open_price, close_price = get_candle_data(symbol, date_str, hour)
        result = resolve_market(open_price, close_price)
        print(f"recommendation: {result}")
    except Exception as e:
        print(f"Failed to resolve market due to an error: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()