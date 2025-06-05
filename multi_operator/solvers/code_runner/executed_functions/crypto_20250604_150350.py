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
        "limit": 1000  # Adjust based on the maximum allowed by the API
    }
    
    try:
        # Try fetching data from the proxy API first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy API failed, error: {e}. Falling back to primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary API also failed, error: {e}.")
            return None

def convert_to_utc_timestamp(date_str, timezone_str="UTC"):
    """
    Converts a date string to a UTC timestamp.
    """
    local_tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    local_datetime = local_tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    return int(utc_datetime.timestamp() * 1000)

def check_new_high_in_may():
    """
    Checks if there was a new all-time high for XRPUSDT in May 2025.
    """
    symbol = "XRPUSDT"
    interval = "1m"
    start_time_may = convert_to_utc_timestamp("2025-05-01 00:00:00", "US/Eastern")
    end_time_may = convert_to_utc_timestamp("2025-05-31 23:59:59", "US/Eastern")
    
    # Fetch historical data before May to find the previous all-time high
    end_time_april = convert_to_utc_timestamp("2025-04-30 23:59:59", "US/Eastern")
    historical_data = fetch_data_from_binance(symbol, interval, 0, end_time_april)
    
    if not historical_data:
        return "p4"  # Unable to fetch data
    
    # Determine the highest price before May
    all_time_high = max(float(candle[2]) for candle in historical_data)
    
    # Fetch May data to check for new highs
    may_data = fetch_data_from_binance(symbol, interval, start_time_may, end_time_may)
    
    if not may_data:
        return "p4"  # Unable to fetch data
    
    # Check if any May price exceeds the previous all-time high
    for candle in may_data:
        if float(candle[2]) > all_time_high:
            return "p2"  # New all-time high found
    
    return "p1"  # No new all-time high

# Main execution
if __name__ == "__main__":
    result = check_new_high_in_may()
    print(f"recommendation: {result}")