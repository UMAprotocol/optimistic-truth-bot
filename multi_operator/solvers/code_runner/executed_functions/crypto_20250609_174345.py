import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# Constants for the API endpoints
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

def fetch_price_from_dexscreener(start_time, end_time):
    """
    Fetches the highest price of Fartcoin/SOL from Dexscreener within the specified time range.
    Args:
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.
    Returns:
        float: The highest price found, or None if no data could be fetched.
    """
    params = {
        "symbol": "FartcoinSOL",
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(f"{PROXY_URL}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return max(float(candle[2]) for candle in data)  # Index 2 is the 'High' price
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return max(float(candle[2]) for candle in data)
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def main():
    # Define the time range for the query
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Convert to UTC and then to milliseconds since epoch
    start_time_utc = start_date.astimezone(pytz.utc)
    end_time_utc = end_date.astimezone(pytz.utc)
    start_time_ms = int(start_time_utc.timestamp() * 1000)
    end_time_ms = int(end_time_utc.timestamp() * 1000)
    
    # Fetch the highest price from Dexscreener
    highest_price = fetch_price_from_dexscreener(start_time_ms, end_time_ms)
    
    # Determine the resolution based on the highest price
    if highest_price is not None and highest_price >= 2.0:
        print("recommendation: p2")  # Yes, Fartcoin reached $2.00
    else:
        print("recommendation: p1")  # No, Fartcoin did not reach $2.00

if __name__ == "__main__":
    main()