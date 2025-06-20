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
        print(f"Proxy failed with error: {e}. Trying primary API endpoint.")
        # Fallback to the primary API endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary API also failed with error: {e}.")
            return None

def get_candle_data(symbol, target_datetime):
    """
    Converts the target datetime to milliseconds and fetches the candle data for that period.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later in milliseconds

    # Fetch the candle data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        return data[0]  # Return the first (and only) candle
    return None

def main():
    # Define the target date and time
    target_datetime_str = "2025-06-14 21:00:00"
    target_timezone = "America/New_York"
    symbol = "ETHUSDT"

    # Convert string to datetime
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = pytz.timezone(target_timezone).localize(target_datetime)

    # Get candle data
    candle = get_candle_data(symbol, target_datetime)
    if candle:
        open_price = float(candle[1])
        close_price = float(candle[4])
        percentage_change = ((close_price - open_price) / open_price) * 100

        # Determine the resolution based on the percentage change
        if percentage_change >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data fetch failure

if __name__ == "__main__":
    main()