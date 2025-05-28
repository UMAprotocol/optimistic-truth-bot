import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
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
        # Try fetching data using the proxy API first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy API failed, error: {e}. Trying primary API...")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary API also failed, error: {e}")
            return None

def get_candle_data(symbol, date_str, hour):
    """
    Retrieves the closing price for a specific hour candle on a given date for the specified symbol.
    """
    # Convert date and hour to the correct timestamp
    tz = pytz.timezone("America/New_York")
    dt = datetime.strptime(date_str + f" {hour}:00:00", "%Y-%m-%d %H:%M:%S")
    dt = tz.localize(dt)
    start_time = int(dt.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour in milliseconds

    # Fetch data from Binance
    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        return None, None

def main():
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