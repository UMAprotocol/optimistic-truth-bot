import requests
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

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
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the open and close price for a specific 1-hour candle on Binance.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        raise ValueError("No data returned from API.")

def resolve_market():
    """
    Resolves the market based on the open and close prices of the BTC/USDT pair.
    """
    # Define the target datetime for the candle (June 19, 2025, 11:00 AM ET)
    target_datetime = datetime(2025, 6, 19, 11, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "BTCUSDT"

    try:
        open_price, close_price = get_candle_data(symbol, target_datetime)
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    except Exception as e:
        print(f"Error resolving market: {e}")
        return "recommendation: p3"  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    result = resolve_market()
    print(result)