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

def fetch_ethusdt_low_price(start_time, end_time):
    """
    Fetches the lowest price of ETHUSDT from Binance within a given time range.
    
    Args:
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.
    
    Returns:
        float: The lowest price found, or None if no data could be fetched.
    """
    params = {
        "symbol": "ETHUSDT",
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000  # Maximum limit
    }
    
    try:
        # Try fetching from the proxy API first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return min(float(candle[3]) for candle in data)  # Index 3 is the 'Low' price
    except Exception as e:
        print(f"Proxy API failed: {e}, falling back to primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return min(float(candle[3]) for candle in data)
        except Exception as e:
            print(f"Primary API failed: {e}")
            return None

def check_eth_price_dip_to_1600():
    """
    Checks if the price of ETH dipped to $1600 or below in May 2025.
    
    Returns:
        str: 'p1' if no dip, 'p2' if dipped, 'p4' if data is inconclusive.
    """
    # Define the time range for May 2025 in ET timezone
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 5, 1))
    end_date = tz.localize(datetime(2025, 5, 31, 23, 59, 59))
    
    # Convert to UTC and then to milliseconds since epoch
    start_time = int(start_date.astimezone(pytz.utc).timestamp() * 1000)
    end_time = int(end_date.astimezone(pytz.utc).timestamp() * 1000)
    
    # Fetch the lowest price in the given range
    lowest_price = fetch_ethusdt_low_price(start_time, end_time)
    
    if lowest_price is None:
        return "p4"  # Inconclusive data
    elif lowest_price <= 1600:
        return "p2"  # Price dipped to $1600 or below
    else:
        return "p1"  # Price did not dip to $1600

# Main execution
if __name__ == "__main__":
    result = check_eth_price_dip_to_1600()
    print(f"recommendation: {result}")