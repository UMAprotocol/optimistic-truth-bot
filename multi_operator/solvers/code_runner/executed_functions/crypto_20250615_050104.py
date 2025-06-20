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
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            return None

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the closing price of a specific 1-hour candle for the given datetime.
    """
    # Convert datetime to milliseconds
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        return None, None

def main():
    # Define the target date and time
    target_datetime_str = "2025-06-15 00:00:00"
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"

    # Convert string to datetime object in the specified timezone
    tz = pytz.timezone(timezone_str)
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = tz.localize(target_datetime)

    # Get the opening and closing prices of the 1-hour candle starting at the target datetime
    open_price, close_price = get_candle_data(symbol, target_datetime)

    if open_price is not None and close_price is not None:
        # Calculate the percentage change
        change_percentage = ((close_price - open_price) / open_price) * 100

        # Determine the resolution based on the change percentage
        if change_percentage >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data retrieval failure

if __name__ == "__main__":
    main()