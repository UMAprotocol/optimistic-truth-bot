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
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the open and close price for a specific 1-hour candle.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        return None, None

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the open and close prices.
    """
    if close_price is None or open_price is None:
        return "p3"  # Unknown or data not available
    elif close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    # Define the target date and time for the candle
    target_datetime = datetime(2025, 6, 20, 2, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    
    # Symbol for the market
    symbol = "BTCUSDT"
    
    # Get the open and close price for the specified candle
    open_price, close_price = get_candle_data(symbol, target_datetime)
    
    # Resolve the market based on the prices
    result = resolve_market(open_price, close_price)
    
    # Print the result
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()