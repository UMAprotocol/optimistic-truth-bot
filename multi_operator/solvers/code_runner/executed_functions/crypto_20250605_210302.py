import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API = "https://api.binance.com/api/v3"
PROXY_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

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
        # Try fetching data from the proxy API first
        response = requests.get(f"{PROXY_API}/klines", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy API failed, error: {e}. Trying primary API.")
        # Fallback to the primary API if proxy fails
        try:
            response = requests.get(f"{PRIMARY_API}/klines", params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Primary API also failed, error: {e}.")
            return None

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance.
    """
    # Define the time for the 1 hour candle on June 5, 2025, 4 PM ET
    target_time = datetime(2025, 6, 5, 16, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    start_time = int(target_time.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # Fetch the candle data
    candle_data = fetch_price_data("BTCUSDT", "1h", start_time, end_time)
    if candle_data:
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])
        print(f"Open price: {open_price}, Close price: {close_price}")

        # Determine if the price went up or down
        if close_price >= open_price:
            print("recommendation: p2")  # Market resolves to "Up"
        else:
            print("recommendation: p1")  # Market resolves to "Down"
    else:
        print("recommendation: p3")  # Unable to fetch data, resolve as unknown/50-50

if __name__ == "__main__":
    resolve_market()