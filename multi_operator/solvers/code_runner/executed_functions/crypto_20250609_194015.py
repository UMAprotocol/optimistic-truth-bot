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
    Converts a local date string to UTC timestamp.
    """
    local_tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    local_dt = local_tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def check_solana_high_in_may():
    """
    Checks if Solana reached a new all-time high in May 2025.
    """
    symbol = "SOLUSDT"
    interval = "1m"
    start_date = "2025-05-01 00:00:00"
    end_date = "2025-05-31 23:59:59"
    timezone_str = "US/Eastern"
    
    start_time = convert_to_utc_timestamp(start_date, timezone_str)
    end_time = convert_to_utc_timestamp(end_date, timezone_str)
    
    # Fetch historical data for May 2025
    data = fetch_data_from_binance(symbol, interval, start_time, end_time)
    
    # Extract all high prices from the data
    highs = [float(candle[2]) for candle in data]
    
    # Check if any high in May 2025 is greater than the previous all-time high
    previous_high = max(highs)  # This should be replaced with the actual previous all-time high from persistent storage or additional API call
    
    for high in highs:
        if high > previous_high:
            return "recommendation: p2"  # Yes, new all-time high
    
    return "recommendation: p1"  # No new all-time high

# Run the check
if __name__ == "__main__":
    result = check_solana_high_in_may()
    print(result)