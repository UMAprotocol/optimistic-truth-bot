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
PRIMARY_API_ENDPOINT = "https://api.binance.com/api/v3/klines"
PROXY_API_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API for a given symbol within a specified time range.
    Implements a fallback mechanism from proxy to primary endpoint.
    
    Args:
        symbol (str): The symbol to fetch data for, e.g., 'SOLUSDT'.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        list: List of price data or None if both requests fail.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum limit
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        
        try:
            # Fallback to the primary endpoint
            response = requests.get(PRIMARY_API_ENDPOINT, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
    
    return None

def check_price_threshold(data, threshold):
    """
    Checks if any 'High' price in the data exceeds the threshold.
    
    Args:
        data (list): List of price data.
        threshold (float): Price threshold to check against.
    
    Returns:
        bool: True if threshold is exceeded, False otherwise.
    """
    for item in data:
        high_price = float(item[2])  # 'High' price is at index 2
        if high_price >= threshold:
            return True
    return False

def main():
    # Define the symbol and threshold
    symbol = "SOLUSDT"
    threshold = 160.0
    
    # Define the time range for June 2025 in Eastern Time
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 6, 1, 0, 0, 0)).astimezone(pytz.utc)
    end_date = tz.localize(datetime(2025, 6, 30, 23, 59, 59)).astimezone(pytz.utc)
    
    # Convert datetime to milliseconds since epoch
    start_time_ms = int(start_date.timestamp() * 1000)
    end_time_ms = int(end_date.timestamp() * 1000)
    
    # Fetch price data
    data = fetch_price_data(symbol, start_time_ms, end_time_ms)
    
    # Check if the price threshold was exceeded
    if data and check_price_threshold(data, threshold):
        print("recommendation: p2")  # Yes, price reached $160 or higher
    else:
        print("recommendation: p1")  # No, price did not reach $160

if __name__ == "__main__":
    main()