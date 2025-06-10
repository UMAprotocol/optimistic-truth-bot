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
        return data
    except Exception as e:
        print(f"Proxy failed with error: {e}, falling back to primary API.")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def get_candle_data(symbol, date_str, hour):
    """
    Retrieves the closing price for a specific hour candle on a given date.
    """
    # Convert date and hour to the correct timestamp
    date = datetime.strptime(date_str, "%Y-%m-%d")
    date = date.replace(hour=hour, minute=0, second=0, microsecond=0)
    tz = pytz.timezone("America/New_York")
    date = tz.localize(date)
    start_time = int(date.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour in milliseconds

    # Fetch the candle data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        return None, None

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the price movement.
    """
    if close_price is None or open_price is None:
        return "p3"  # Unknown or data not available
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    symbol = "BTCUSDT"
    date_str = "2025-05-29"
    hour = 10  # 10 AM ET

    open_price, close_price = get_candle_data(symbol, date_str, hour)
    result = resolve_market(open_price, close_price)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()