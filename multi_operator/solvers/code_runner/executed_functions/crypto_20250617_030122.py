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
    Fetches price data from Binance API with a fallback to a proxy endpoint.
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
    except Exception as proxy_error:
        print(f"Proxy endpoint failed: {proxy_error}, falling back to primary endpoint")
        try:
            # Fallback to the primary endpoint if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as primary_error:
            print(f"Primary endpoint also failed: {primary_error}")
            return None

def get_candle_data(symbol, target_datetime):
    """
    Converts the target datetime to UTC and fetches the 1-hour candle data for the specified symbol.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch the candle data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        return None, None

def main():
    # Define the target date and time
    target_datetime_str = "2025-06-16 22:00:00"
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"

    # Convert string to datetime object
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = pytz.timezone(timezone_str).localize(target_datetime)

    # Convert to UTC
    target_datetime_utc = target_datetime.astimezone(pytz.utc)

    # Get the opening and closing prices of the 1-hour candle
    open_price, close_price = get_candle_data(symbol, target_datetime_utc)

    if open_price is not None and close_price is not None:
        # Determine if the price went up or down
        if close_price >= open_price:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data fetch failure

if __name__ == "__main__":
    main()