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
            return data[0]
    except Exception as e:
        print(f"Proxy failed with error: {e}, falling back to primary endpoint.")
        # Fallback to the primary endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Primary endpoint also failed with error: {e}")
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
    candle_data = fetch_price_data(symbol, "1h", start_time, end_time)
    if candle_data:
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])
        return open_price, close_price
    else:
        return None, None

def main():
    """
    Main function to determine if the Bitcoin price went up or down.
    """
    symbol = "BTCUSDT"
    date_str = "2025-05-28"
    hour = 11  # 11 AM ET

    open_price, close_price = get_candle_data(symbol, date_str, hour)
    if open_price is not None and close_price is not None:
        if close_price >= open_price:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data fetch failure

if __name__ == "__main__":
    main()