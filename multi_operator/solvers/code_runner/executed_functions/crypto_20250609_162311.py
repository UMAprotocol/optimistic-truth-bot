import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
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
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_ENDPOINT, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return max(float(candle[2]) for candle in data)
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            return None

def check_eth_price_threshold():
    """
    Checks if the Ethereum price reached $3000 at any point in May 2025.
    
    Returns:
        str: 'p1' if the price never reached $3000, 'p2' if it did, 'p3' if unknown.
    """
    # Define the time range for May 2025 in Eastern Time
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 5, 1))
    end_date = tz.localize(datetime(2025, 5, 31, 23, 59, 59))
    
    # Convert to UTC and then to milliseconds since epoch
    start_time_utc = int(start_date.astimezone(pytz.utc).timestamp() * 1000)
    end_time_utc = int(end_date.astimezone(pytz.utc).timestamp() * 1000)
    
    # Fetch the highest price in the given time range
    high_price = fetch_eth_high_price(start_time_utc, end_time_utc)
    
    if high_price is None:
        return "p3"  # Unknown if no data could be retrieved
    elif high_price >= 3000:
        return "p2"  # Yes, price reached $3000
    else:
        return "p1"  # No, price did not reach $3000

def main():
    result = check_eth_price_threshold()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()