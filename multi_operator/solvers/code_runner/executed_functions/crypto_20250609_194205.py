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
        "limit": 1000  # Adjust based on the maximum results needed per API call
    }
    
    try:
        # Try fetching data from the proxy API first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy API failed, error: {e}. Falling back to primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Primary API also failed, error: {e}.")
            return None

def convert_to_utc_timestamp(date_str, time_str, timezone_str):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    local_tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    local_dt = local_tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    symbol = "SOLUSDT"
    interval = "1m"
    timezone_str = "US/Eastern"
    start_date = "2025-05-01"
    end_date = "2025-05-31"
    
    # Convert start and end dates to UTC timestamps
    start_time = convert_to_utc_timestamp(start_date, "00:00:00", timezone_str)
    end_time = convert_to_utc_timestamp(end_date, "23:59:59", timezone_str)
    
    # Fetch historical data from Binance
    historical_data = fetch_data_from_binance(symbol, interval, start_time, end_time)
    
    if historical_data:
        # Extract all high prices from the data
        high_prices = [float(candle[2]) for candle in historical_data]
        current_max_high = max(high_prices)
        
        # Fetch previous all-time high before May 2025
        previous_end_time = start_time - 1  # One millisecond before May starts
        previous_data = fetch_data_from_binance(symbol, interval, 0, previous_end_time)  # From the start of the trading
        
        if previous_data:
            previous_high_prices = [float(candle[2]) for candle in previous_data]
            previous_max_high = max(previous_high_prices)
            
            # Compare the current max high with the previous all-time high
            if current_max_high > previous_max_high:
                print("recommendation: p2")  # Yes, new all-time high in May
            else:
                print("recommendation: p1")  # No new all-time high in May
        else:
            print("recommendation: p4")  # Unable to fetch previous data
    else:
        print("recommendation: p4")  # Unable to fetch current data

if __name__ == "__main__":
    main()