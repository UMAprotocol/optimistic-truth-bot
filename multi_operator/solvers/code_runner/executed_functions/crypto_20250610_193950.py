import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_eth_high_price(start_time, end_time):
    """
    Fetches the highest price of Ethereum (ETHUSDT) from Binance within a given time range.
    
    Args:
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.
    
    Returns:
        float: The highest price of Ethereum found in the time range.
    """
    params = {
        "symbol": "ETHUSDT",
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return max(float(candle[2]) for candle in data)  # High price is at index 2
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return max(float(candle[2]) for candle in data)
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            return None

def check_eth_price_threshold():
    """
    Checks if the Ethereum price reached $2800 at any point in June 2025.
    
    Returns:
        str: Recommendation based on the price check.
    """
    # Define the time range for June 2025 in Eastern Time
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 6, 1))
    end_date = tz.localize(datetime(2025, 6, 30, 23, 59, 59))
    
    # Convert to UTC and then to milliseconds since epoch
    start_time = int(start_date.astimezone(pytz.utc).timestamp() * 1000)
    end_time = int(end_date.astimezone(pytz.utc).timestamp() * 1000)
    
    # Fetch the highest price in the given time range
    high_price = fetch_eth_high_price(start_time, end_time)
    
    if high_price is not None:
        if high_price >= 2800:
            return "recommendation: p2"  # Yes, it reached $2800 or higher
        else:
            return "recommendation: p1"  # No, it did not reach $2800
    else:
        return "recommendation: p3"  # Unknown or data fetch error

if __name__ == "__main__":
    result = check_eth_price_threshold()
    print(result)