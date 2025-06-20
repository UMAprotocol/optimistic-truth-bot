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
PRIMARY_API_ENDPOINT = "https://api.binance.com/api/v3/klines"
PROXY_API_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_eth_high_price(start_time, end_time):
    """
    Fetches the highest price of Ethereum (ETHUSDT) from Binance within a given time range.
    
    Args:
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.
    
    Returns:
        float: The highest price of Ethereum found in the time range or None if not found.
    """
    params = {
        "symbol": "ETHUSDT",
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(PROXY_API_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return max(float(candle[2]) for candle in data)  # High price is at index 2
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_ENDPOINT, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return max(float(candle[2]) for candle in data)
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_eth_price_threshold():
    """
    Checks if the Ethereum price reached $2700 at any point in June 2025.
    
    Returns:
        str: 'recommendation: p1' if Ethereum did not reach $2700,
             'recommendation: p2' if Ethereum reached $2700,
             'recommendation: p4' if unable to determine.
    """
    # Define the time range for June 2025 in Eastern Time
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 6, 1, 0, 0, 0)).astimezone(pytz.utc)
    end_date = tz.localize(datetime(2025, 6, 30, 23, 59, 59)).astimezone(pytz.utc)
    
    # Convert to milliseconds since epoch
    start_time_ms = int(start_date.timestamp() * 1000)
    end_time_ms = int(end_date.timestamp() * 1000)
    
    # Fetch the highest price in the range
    high_price = fetch_eth_high_price(start_time_ms, end_time_ms)
    
    if high_price is None:
        return "recommendation: p4"
    elif high_price >= 2700.00:
        return "recommendation: p2"
    else:
        return "recommendation: p1"

if __name__ == "__main__":
    result = check_eth_price_threshold()
    print(result)