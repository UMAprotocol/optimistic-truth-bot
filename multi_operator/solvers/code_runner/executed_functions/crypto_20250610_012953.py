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
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_candle_data(symbol, target_date, target_hour):
    """
    Retrieves the closing price of a specific hourly candle.
    """
    # Convert local time to UTC timestamp
    tz = pytz.timezone("US/Eastern")
    local_dt = tz.localize(datetime(target_date.year, target_date.month, target_date.day, target_hour, 0, 0))
    utc_dt = local_dt.astimezone(pytz.utc)
    
    start_time = int(utc_dt.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour in milliseconds
    
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    return None, None

def resolve_market():
    """
    Resolves the market based on the price change of the BTC/USDT pair.
    """
    target_date = datetime(2025, 5, 30)
    symbol = "BTCUSDT"
    target_hour = 18  # 6 PM ET
    
    open_price, close_price = get_candle_data(symbol, target_date, target_hour)
    
    if open_price is None or close_price is None:
        return "recommendation: p4"  # Unable to resolve
    
    if close_price >= open_price:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

if __name__ == "__main__":
    result = resolve_market()
    print(result)