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

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "startTime": start_time,
        "endTime": end_time
    }
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy failed, error: {e}, trying primary API endpoint.")
        # Fallback to the primary API endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            print(f"Both proxy and primary API requests failed: {e}")
            return None

def get_candle_data(symbol, target_datetime):
    """
    Converts the target datetime to the correct format and fetches the candle data.
    """
    # Convert datetime to milliseconds
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch the candle data
    data = fetch_price_data(symbol, start_time, end_time)
    if data and len(data) > 0:
        # Extract the opening and closing prices from the first candle
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        return None, None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price movement of the specified symbol at the given datetime.
    """
    open_price, close_price = get_candle_data(symbol, target_datetime)
    if open_price is None or close_price is None:
        return "recommendation: p4"  # Unable to fetch data

    # Determine if the price went up or down
    if close_price >= open_price:
        return "recommendation: p2"  # Market resolves to "Up"
    else:
        return "recommendation: p1"  # Market resolves to "Down"

def main():
    # Example usage
    symbol = "BTCUSDT"
    target_datetime = datetime(2025, 6, 8, 9, 0, 0, tzinfo=pytz.timezone("America/New_York"))
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()