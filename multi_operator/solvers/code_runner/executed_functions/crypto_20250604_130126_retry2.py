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
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, startTime, endTime, use_proxy=False):
    """
    Fetches data from Binance API.
    Args:
        symbol (str): The symbol to fetch data for.
        interval (str): The interval of the data.
        startTime (int): Start time in milliseconds.
        endTime (int): End time in milliseconds.
        use_proxy (bool): Whether to use the proxy endpoint.
    Returns:
        dict: The API response.
    """
    url = PROXY_BINANCE_API if use_proxy else PRIMARY_BINANCE_API
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": startTime,
        "endTime": endTime,
        "limit": 1
    }
    try:
        response = requests.get(f"{url}/klines", params=params)
        response.raise_for_status()
        data = response.json()
        return data[0]  # Return the first (and only) entry
    except requests.RequestException as e:
        if not use_proxy:
            raise e  # If already using primary, re-raise exception
        print("Proxy failed, trying primary endpoint")
        return fetch_binance_data(symbol, interval, startTime, endTime, use_proxy=False)

def get_price_change(symbol, date_str, hour):
    """
    Determines if the price of a symbol has gone up or down at a specific hour.
    Args:
        symbol (str): The trading symbol.
        date_str (str): The date in YYYY-MM-DD format.
        hour (int): The hour in 24-hour format.
    Returns:
        str: 'p1' if down, 'p2' if up, 'p3' if unknown.
    """
    tz = pytz.timezone("America/New_York")
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    dt = tz.localize(datetime(dt.year, dt.month, dt.day, hour, 0, 0))
    start_time = int(dt.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    try:
        data = fetch_binance_data(symbol, "1h", start_time, end_time, use_proxy=True)
        open_price = float(data[1])
        close_price = float(data[4])
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    except Exception as e:
        print(f"Error fetching or processing data: {e}")
        return "p3"  # Unknown

def main():
    symbol = "BTCUSDT"
    date_str = "2025-06-04"
    hour = 5  # 5 AM ET
    result = get_price_change(symbol, date_str, hour)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()