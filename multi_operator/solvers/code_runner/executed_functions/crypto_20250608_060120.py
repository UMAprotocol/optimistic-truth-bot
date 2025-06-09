import requests
from datetime import datetime, timedelta, timezone
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
    try:
        # Try fetching data using the proxy URL first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary API endpoint.")
        # Fallback to the primary API endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            raise

def get_price_change(symbol, target_date):
    """
    Determines the price change for the specified symbol on Binance at the given date.
    """
    # Convert target date to the beginning of the hour in UTC
    target_datetime = datetime.strptime(target_date, "%Y-%m-%d %H:%M:%S")
    target_datetime = pytz.timezone("US/Eastern").localize(target_datetime).astimezone(pytz.utc)
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch data
    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = ((close_price - open_price) / open_price) * 100
        return price_change
    else:
        return None

def main():
    """
    Main function to determine if the Bitcoin price went up or down.
    """
    target_date = "2025-06-08 01:00:00"
    symbol = "BTCUSDT"
    try:
        price_change = get_price_change(symbol, target_date)
        if price_change is not None:
            if price_change >= 0:
                print("recommendation: p2")  # Up
            else:
                print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # Unknown/50-50
    except Exception as e:
        print(f"Failed to determine price change due to error: {e}")
        print("recommendation: p3")  # Unknown/50-50

if __name__ == "__main__":
    main()