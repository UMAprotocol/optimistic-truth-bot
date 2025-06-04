import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000  # Maximum limit
    }
    
    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def convert_to_utc_timestamp(date_str, timezone_str='UTC'):
    """
    Converts a date string to a UTC timestamp.
    """
    local_tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    local_datetime = local_tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    return int(utc_datetime.timestamp() * 1000)

def check_dogecoin_high_in_may():
    """
    Checks if Dogecoin reached a new all-time high in May 2025.
    """
    # Define the time period for May 2025 in Eastern Time
    start_date = "2025-05-01 00:00:00"
    end_date = "2025-05-31 23:59:59"
    timezone_str = 'US/Eastern'
    
    # Convert to UTC timestamps
    start_timestamp = convert_to_utc_timestamp(start_date, timezone_str)
    end_timestamp = convert_to_utc_timestamp(end_date, timezone_str)
    
    # Fetch historical data for Dogecoin in May 2025
    historical_data = fetch_binance_data("DOGEUSDT", "1m", start_timestamp, end_timestamp)
    
    if not historical_data:
        print("Failed to retrieve data.")
        return "recommendation: p4"
    
    # Determine the highest price in May 2025
    may_high = max([float(candle[2]) for candle in historical_data])  # Index 2 is 'High' price
    
    # Fetch historical data before May 2025 to find the previous all-time high
    previous_data = fetch_binance_data("DOGEUSDT", "1m", 0, start_timestamp - 1)
    
    if not previous_data:
        print("Failed to retrieve previous data.")
        return "recommendation: p4"
    
    previous_high = max([float(candle[2]) for candle in previous_data])
    
    # Compare the highs to determine the resolution
    if may_high > previous_high:
        return "recommendation: p2"  # Yes, new all-time high
    else:
        return "recommendation: p1"  # No new all-time high

# Run the function and print the result
if __name__ == "__main__":
    result = check_dogecoin_high_in_may()
    print(result)