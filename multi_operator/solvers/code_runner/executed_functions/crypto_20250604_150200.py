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

def fetch_data_from_binance(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000  # Adjust based on the maximum results needed per API call
    }
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def convert_to_utc_timestamp(date_str, timezone_str):
    """
    Converts a local date string to UTC timestamp in milliseconds.
    """
    local_tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    local_datetime = local_tz.localize(naive_datetime, is_dst=None)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    return int(utc_datetime.timestamp() * 1000)

def check_xrp_high_in_may():
    """
    Checks if XRP reached a new all-time high in May 2025.
    """
    symbol = "XRPUSDT"
    interval = "1m"
    start_time = convert_to_utc_timestamp("2025-05-01 00:00:00", "US/Eastern")
    end_time = convert_to_utc_timestamp("2025-05-31 23:59:59", "US/Eastern")
    
    # Fetch historical data before May to find the previous all-time high
    historical_end_time = start_time - 1  # One millisecond before May starts
    historical_data = fetch_data_from_binance(symbol, interval, 0, historical_end_time)
    previous_high = max(float(item[2]) for item in historical_data) if historical_data else 0
    
    # Fetch May data to check for new highs
    may_data = fetch_data_from_binance(symbol, interval, start_time, end_time)
    may_high = max(float(item[2]) for item in may_data) if may_data else 0
    
    # Determine if a new all-time high was reached
    if may_high > previous_high:
        print("recommendation: p2")  # Yes, new all-time high
    else:
        print("recommendation: p1")  # No new all-time high

if __name__ == "__main__":
    check_xrp_high_in_may()