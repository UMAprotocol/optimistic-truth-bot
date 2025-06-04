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

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server if the primary fails.
    
    Args:
        symbol (str): The symbol to fetch data for, e.g., 'XRPUSDT'
        start_time (int): Start time in milliseconds since the epoch
        end_time (int): End time in milliseconds since the epoch
    
    Returns:
        list: List of price data or None if both requests fail
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum allowed by Binance for one request
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_xrp_dip_to_two_dollars():
    """
    Checks if XRP dipped to $2.00 or lower in May 2025.
    
    Returns:
        str: 'p1' if no dip, 'p2' if dipped, 'p3' if unknown, 'p4' if error
    """
    # Define the time range for May 2025 in Eastern Time
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 5, 1))
    end_date = tz.localize(datetime(2025, 5, 31, 23, 59))
    
    # Convert to UTC and then to milliseconds since epoch
    start_time_utc = int(start_date.astimezone(pytz.utc).timestamp() * 1000)
    end_time_utc = int(end_date.astimezone(pytz.utc).timestamp() * 1000)
    
    # Fetch price data
    data = fetch_price_data("XRPUSDT", start_time_utc, end_time_utc)
    
    if data:
        # Check if any 'Low' price in the data is $2.00 or lower
        for candle in data:
            low_price = float(candle[3])  # 'Low' price is the fourth element in the list
            if low_price <= 2.00:
                return "p2"  # Yes, dipped to $2.00 or lower
        return "p1"  # No dip to $2.00 or lower
    else:
        return "p4"  # Unable to determine due to API failure

# Main execution
if __name__ == "__main__":
    result = check_xrp_dip_to_two_dollars()
    print(f"recommendation: {result}")