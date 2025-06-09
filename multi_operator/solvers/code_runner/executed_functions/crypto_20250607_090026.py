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
        float: The closing price of the interval.
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
    Resolves the market based on the price change of BTC/USDT on Binance.
    """
    # Define the time for the 1 hour candle starting at 4 AM ET on June 7, 2025
    target_date = datetime(2025, 6, 7, 4, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    start_time = int(target_date.timestamp() * 1000)
    end_time = int((target_date + timedelta(hours=1)).timestamp() * 1000)
    
    # Fetch the closing price for the specified interval
    closing_price_start = fetch_price_data("BTCUSDT", "1h", start_time, start_time + 60000)
    closing_price_end = fetch_price_data("BTCUSDT", "1h", end_time - 60000, end_time)
    
    if closing_price_start is None or closing_price_end is None:
        print("recommendation: p4")  # Unable to fetch data
    elif closing_price_end >= closing_price_start:
        print("recommendation: p2")  # Price went up or stayed the same
    else:
        print("recommendation: p1")  # Price went down

if __name__ == "__main__":
    resolve_market()