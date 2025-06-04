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
    Fetches the lowest price of ETHUSDT from Binance within the given time range.
    
    Args:
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        float: The lowest price found, or None if no data could be fetched.
    """
    params = {
        "symbol": "ETHUSDT",
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return min(float(candle[3]) for candle in data)  # Index 3 is the 'Low' price in each candle
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return min(float(candle[3]) for candle in data)
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_eth_price_dip_to_1200():
    """
    Checks if the price of ETH dipped to $1200 or below in May 2025.
    
    Returns:
        str: 'p1' if no dip, 'p2' if dipped, 'p3' if unknown.
    """
    # Define the time range for May 2025 in Eastern Time
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 5, 1))
    end_date = tz.localize(datetime(2025, 5, 31, 23, 59))
    
    # Convert to UTC and then to milliseconds
    start_time_utc = int(start_date.astimezone(pytz.utc).timestamp() * 1000)
    end_time_utc = int(end_date.astimezone(pytz.utc).timestamp() * 1000)
    
    # Fetch the lowest price in the range
    lowest_price = fetch_ethusdt_low_price(start_time_utc, end_time_utc)
    
    if lowest_price is None:
        return "p3"  # Unknown if no data could be fetched
    elif lowest_price <= 1200.00:
        return "p2"  # Yes, dipped to $1200 or below
    else:
        return "p1"  # No, did not dip to $1200

# Main execution
if __name__ == "__main__":
    result = check_eth_price_dip_to_1200()
    print(f"recommendation: {result}")