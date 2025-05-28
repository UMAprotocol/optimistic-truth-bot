import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configurations
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_PRIMARY_URL = "https://api.binance.com/api/v3"
BINANCE_PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint.
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
        # Try proxy endpoint first
        response = requests.get(f"{BINANCE_PROXY_URL}/klines", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{BINANCE_PRIMARY_URL}/klines", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the closing price of the 1-hour candle for the specified datetime.
    """
    # Convert datetime to milliseconds
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    data = fetch_binance_data(symbol, start_time, end_time)
    if data and len(data) > 0:
        close_price = float(data[0][4])  # Closing price
        open_price = float(data[0][1])  # Opening price
        return close_price, open_price
    else:
        return None, None

def resolve_market():
    """
    Resolves the market based on the price movement of the BTC/USDT pair on Binance.
    """
    target_datetime = datetime(2025, 5, 28, 1, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    symbol = "BTCUSDT"
    close_price, open_price = get_candle_data(symbol, target_datetime)

    if close_price is not None and open_price is not None:
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50 due to data retrieval failure

if __name__ == "__main__":
    result = resolve_market()
    print(result)