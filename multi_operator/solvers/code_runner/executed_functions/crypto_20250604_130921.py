import requests
from datetime import datetime, timedelta
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

def fetch_data_from_binance(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary request fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

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

    # Fetch the candle data
    data = fetch_data_from_binance(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return close_price, open_price
    else:
        return None, None

def main():
    """
    Main function to determine if the Bitcoin price went up or down for the specified candle.
    """
    symbol = "BTCUSDT"
    date_str = "2025-05-31"
    hour = 10  # 10 AM ET

    close_price, open_price = get_candle_data(symbol, date_str, hour)
    if close_price is not None and open_price is not None:
        if close_price >= open_price:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 if data is not available

if __name__ == "__main__":
    main()