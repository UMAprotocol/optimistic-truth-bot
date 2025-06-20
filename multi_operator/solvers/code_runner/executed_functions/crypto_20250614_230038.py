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
    
    Args:
        symbol (str): The symbol to fetch data for, e.g., 'BTCUSDT'.
        interval (str): The interval of the klines data, e.g., '1h'.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        float: The percentage change of the price if data is available, otherwise None.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }
    
    try:
        # Try fetching data from the proxy API first
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return ((close_price - open_price) / open_price) * 100
    except Exception as e:
        print(f"Proxy API failed, error: {e}. Trying primary API...")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            if data:
                open_price = float(data[0][1])
                close_price = float(data[0][4])
                return ((close_price - open_price) / open_price) * 100
        except Exception as e:
            print(f"Primary API failed, error: {e}")
            return None

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance at a specific time.
    """
    # Define the specific time and date
    target_date = datetime(2025, 6, 14, 18, 0, 0)  # June 14, 2025, 6 PM ET
    et_timezone = pytz.timezone('US/Eastern')
    target_date = et_timezone.localize(target_date)
    utc_target_date = target_date.astimezone(pytz.utc)
    
    # Convert to milliseconds since this is what Binance API expects
    start_time = int(utc_target_date.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later
    
    # Fetch the price change percentage
    price_change = fetch_price_data("BTCUSDT", "1h", start_time, end_time)
    
    if price_change is not None:
        if price_change >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data fetch failure

if __name__ == "__main__":
    resolve_market()