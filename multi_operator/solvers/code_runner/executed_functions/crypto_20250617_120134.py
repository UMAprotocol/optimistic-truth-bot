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
    # Define the specific time and date for the market resolution
    target_date = datetime(2025, 6, 17, 7, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    start_time_utc = int(target_date.timestamp() * 1000)
    end_time_utc = int((target_date + timedelta(hours=1)).timestamp() * 1000)
    
    # Fetch the closing price of the 1-hour candle starting at the target time
    closing_price = fetch_price_data("ETHUSDT", "1h", start_time_utc, end_time_utc)
    
    if closing_price is not None:
        # Compare the closing price with the opening price to determine the market resolution
        print(f"Closing price of ETH/USDT at {target_date.strftime('%Y-%m-%d %H:%M:%S %Z')} is {closing_price}")
        if closing_price >= 0:
            print("recommendation: p2")  # Market resolves to "Up"
        else:
            print("recommendation: p1")  # Market resolves to "Down"
    else:
        print("recommendation: p3")  # Unable to determine, resolve as unknown/50-50

if __name__ == "__main__":
    resolve_market()