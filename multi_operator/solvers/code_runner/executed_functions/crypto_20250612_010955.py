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

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
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
        # Try fetching data using the proxy URL first
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary API endpoint.")
        # If proxy fails, fallback to the primary API endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def get_price_change(symbol, target_datetime):
    """
    Calculates the price change percentage for the specified symbol at the target datetime.
    """
    # Convert target datetime to the correct format for the API call
    utc_time = target_datetime.astimezone(pytz.utc)
    start_time = int(utc_time.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # Fetch data
    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change_percent = ((close_price - open_price) / open_price) * 100
        return price_change_percent
    else:
        return None

def main():
    # Define the target datetime and symbol
    target_datetime = datetime(2025, 6, 11, 20, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "BTCUSDT"

    # Get the price change percentage
    price_change = get_price_change(symbol, target_datetime)

    # Determine the resolution based on the price change
    if price_change is None:
        print("recommendation: p3")  # Unknown or data fetch error
    elif price_change >= 0:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

if __name__ == "__main__":
    main()