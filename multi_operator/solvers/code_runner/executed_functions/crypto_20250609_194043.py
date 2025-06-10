import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables
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
        "limit": 1000  # Adjust based on the maximum data needed
    }
    
    try:
        # Try fetching from the proxy first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy failed with error {e}, trying primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Primary API also failed with error {e}.")
            raise

def convert_to_utc_timestamp(date_str, time_str='00:00:00', timezone_str='US/Eastern'):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    local_tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    local_dt = local_tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def check_solana_high_in_may():
    """
    Checks if Solana reached a new all-time high in May 2025.
    """
    # Define the time period for May 2025 in Eastern Time
    start_date = "2025-05-01"
    end_date = "2025-05-31"
    start_time = convert_to_utc_timestamp(start_date, "00:00:00", "US/Eastern")
    end_time = convert_to_utc_timestamp(end_date, "23:59:59", "US/Eastern")
    
    # Fetch historical data for May 2025
    may_data = fetch_data_from_binance("SOLUSDT", "1m", start_time, end_time)
    
    # Extract the highest price in May 2025
    may_high = max([float(candle[2]) for candle in may_data])
    
    # Fetch historical data before May 2025 to find the previous all-time high
    previous_data = fetch_data_from_binance("SOLUSDT", "1m", 0, start_time - 1)
    previous_high = max([float(candle[2]) for candle in previous_data])
    
    # Compare the highs to determine the resolution
    if may_high > previous_high:
        return "p2"  # Yes, new all-time high
    else:
        return "p1"  # No new all-time high

def main():
    try:
        result = check_solana_high_in_may()
        print(f"recommendation: {result}")
    except Exception as e:
        print(f"Failed to process due to error: {e}")
        print("recommendation: p3")  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    main()