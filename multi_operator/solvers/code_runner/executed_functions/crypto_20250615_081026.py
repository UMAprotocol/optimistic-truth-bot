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
        if data:
            return data
    except Exception as e:
        print(f"Proxy failed with error: {e}, falling back to primary API.")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the closing price of a specific 1-hour candle for the given datetime.
    """
    # Convert datetime to milliseconds
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch the candle data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        # Extract the closing price from the first candle
        close_price = float(data[0][4])
        return close_price
    else:
        return None

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance at a specific time.
    """
    # Define the target datetime in Eastern Time
    target_datetime_str = "2025-06-15 03:00:00"
    eastern = pytz.timezone("US/Eastern")
    target_datetime = eastern.localize(datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S"))

    # Get the closing price of the 1-hour candle starting at the target time
    initial_price = get_candle_data("BTCUSDT", target_datetime)
    if initial_price is None:
        print("recommendation: p4")
        return

    # Get the closing price of the next 1-hour candle
    next_candle_datetime = target_datetime + timedelta(hours=1)
    next_price = get_candle_data("BTCUSDT", next_candle_datetime)
    if next_price is None:
        print("recommendation: p4")
        return

    # Determine the market resolution based on the price change
    if next_price >= initial_price:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

if __name__ == "__main__":
    resolve_market()