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
        symbol (str): The symbol to fetch data for, e.g., 'ETHUSDT'.
        interval (str): The interval of the klines data, e.g., '1h'.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        float: The closing price of the symbol at the specified time.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy API first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy API failed, error: {e}. Falling back to primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data[0][4])  # Closing price
        except Exception as e:
            print(f"Primary API also failed, error: {e}.")
            return None

def resolve_market():
    """
    Resolves the market based on the price change of ETH/USDT on Binance.
    """
    # Define the time for the 1H candle on June 12, 1 PM ET
    target_time = datetime(2025, 6, 12, 13, 0, 0)  # June 12, 2025, 1 PM ET
    tz = pytz.timezone("US/Eastern")
    target_time = tz.localize(target_time)
    target_time_utc = target_time.astimezone(pytz.utc)
    
    # Convert to milliseconds for the API call
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later
    
    # Fetch the closing price for the 1H candle
    closing_price_start = fetch_price_data("ETHUSDT", "1h", start_time_ms, start_time_ms + 60000)
    closing_price_end = fetch_price_data("ETHUSDT", "1h", end_time_ms - 60000, end_time_ms)
    
    if closing_price_start is None or closing_price_end is None:
        print("recommendation: p3")  # Unknown/50-50 if data fetching fails
    elif closing_price_end >= closing_price_start:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

if __name__ == "__main__":
    resolve_market()