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
PRIMARY_API_ENDPOINT = "https://api.binance.com/api/v3/klines"
PROXY_API_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_API_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
        else:
            raise ValueError("No data returned from proxy endpoint.")
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_candle_data(symbol, date_str, hour):
    """
    Retrieves the closing price for a specific hour candle on a given date for the specified symbol.
    """
    # Convert date and hour to the correct timestamp in milliseconds
    date = datetime.strptime(date_str, "%Y-%m-%d")
    date = date.replace(hour=hour, minute=0, second=0, microsecond=0)
    tz = pytz.timezone("America/New_York")
    date = tz.localize(date)
    start_time = int(date.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    # Fetch the candle data
    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return close_price, open_price
    else:
        raise Exception("Failed to retrieve data.")

def resolve_market():
    """
    Resolves the market based on the price movement of the BTC/USDT pair on Binance.
    """
    try:
        close_price, open_price = get_candle_data("BTCUSDT", "2025-05-28", 5)
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    except Exception as e:
        print(f"Error resolving market: {e}")
        return "recommendation: p3"  # Unknown/50-50

if __name__ == "__main__":
    result = resolve_market()
    print(result)