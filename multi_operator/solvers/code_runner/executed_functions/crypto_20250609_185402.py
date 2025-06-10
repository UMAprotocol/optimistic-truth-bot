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
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_eth_high_price(start_time, end_time):
    """
    Fetches the highest price of Ethereum (ETHUSDT) from Binance within a given time range.
    
    Args:
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.
    
    Returns:
        float: The highest price of Ethereum found in the time range, or None if not found.
    """
    params = {
        "symbol": "ETHUSDT",
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return max(float(candle[2]) for candle in data)  # High price is at index 2
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            if data:
                return max(float(candle[2]) for candle in data)  # High price is at index 2
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_eth_price_in_may_2025():
    """
    Checks if the price of Ethereum reached $4000 at any point in May 2025.
    
    Returns:
        str: 'recommendation: p1' if the price never reached $4000,
             'recommendation: p2' if the price reached $4000 or more,
             'recommendation: p3' if the result is unknown.
    """
    # Define the time range for May 2025 in Eastern Time
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 5, 1))
    end_date = tz.localize(datetime(2025, 5, 31, 23, 59))
    
    # Convert to UTC and then to milliseconds since epoch
    start_time_utc = int(start_date.astimezone(pytz.utc).timestamp() * 1000)
    end_time_utc = int(end_date.astimezone(pytz.utc).timestamp() * 1000)
    
    # Fetch the highest price in May 2025
    highest_price = fetch_eth_high_price(start_time_utc, end_time_utc)
    
    if highest_price is None:
        return "recommendation: p3"  # Unknown result if data fetching failed
    elif highest_price >= 4000:
        return "recommendation: p2"  # Yes, price reached $4000 or more
    else:
        return "recommendation: p1"  # No, price never reached $4000

if __name__ == "__main__":
    result = check_eth_price_in_may_2025()
    print(result)