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

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    
    Args:
        symbol (str): The symbol to fetch data for (e.g., 'ETHUSDT').
        interval (str): The interval of the klines data (e.g., '1h').
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        float: The closing price of the symbol at the specified time.
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
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy API failed, error: {e}. Falling back to primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Closing price
        except Exception as e:
            print(f"Primary API also failed, error: {e}.")
            return None

def resolve_market():
    """
    Resolves the market based on the Ethereum price change.
    """
    # Define the time and symbol
    symbol = "ETHUSDT"
    interval = "1h"
    target_time = datetime(2025, 6, 12, 1, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    target_time_utc = target_time.astimezone(pytz.utc)
    
    # Convert datetime to milliseconds
    start_time = int(target_time_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later
    
    # Fetch the closing price at the start and end of the interval
    start_price = fetch_price_data(symbol, interval, start_time, start_time)
    end_price = fetch_price_data(symbol, interval, end_time, end_time)
    
    if start_price is None or end_price is None:
        print("recommendation: p4")  # Unable to fetch data
    else:
        # Calculate the percentage change
        change_percentage = ((end_price - start_price) / start_price) * 100
        if change_percentage >= 0:
            print("recommendation: p2")  # Market resolves to "Up"
        else:
            print("recommendation: p1")  # Market resolves to "Down"

if __name__ == "__main__":
    resolve_market()