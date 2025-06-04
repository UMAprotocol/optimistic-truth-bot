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
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary API.")
        # Fallback to the primary API if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data

def get_candle_data(symbol, target_date):
    """
    Retrieves the closing price for the specified symbol and date.
    """
    # Convert date to the correct timestamp for the API call
    tz = pytz.timezone("America/New_York")
    naive_datetime = datetime.strptime(target_date + " 16:00:00", "%Y-%m-%d %H:%M:%S")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    
    start_time = int(utc_datetime.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # One hour later
    
    data = fetch_price_data(symbol, start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        raise ValueError("No data returned from API.")

def resolve_market(symbol, target_date):
    """
    Resolves the market based on the price movement.
    """
    try:
        open_price, close_price = get_candle_data(symbol, target_date)
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    except Exception as e:
        print(f"Error resolving market: {e}")
        return "recommendation: p3"  # Unknown/50-50 if error occurs

# Example usage
if __name__ == "__main__":
    result = resolve_market("BTCUSDT", "2025-05-30")
    print(result)