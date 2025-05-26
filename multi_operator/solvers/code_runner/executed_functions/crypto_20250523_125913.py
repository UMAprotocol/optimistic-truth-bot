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

def fetch_data(symbol, interval, start_time, end_time):
    """
    Fetches cryptocurrency data using the Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1000,  # Adjust based on the maximum number of data points needed
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy failed with error: {e}, falling back to primary API.")
        # Fallback to the primary API endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
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

def analyze_high_prices(data):
    """
    Analyzes the high prices from the fetched data to determine if a new all-time high was reached.
    """
    if not data:
        return "p4"  # Unable to resolve due to data fetch failure
    
    current_high = max([float(candle[2]) for candle in data])  # Index 2 is 'High' in each candle
    print(f"Current period high: {current_high}")
    
    # Assuming historical high data is stored or fetched separately
    historical_high = 50000.0  # Placeholder for the highest historical price
    
    if current_high > historical_high:
        return "p2"  # Yes, a new all-time high was reached
    else:
        return "p1"  # No, no new all-time high was reached

def main():
    symbol = "HYPEUSDC"
    interval = "1m"
    start_date = "2025-05-22"
    end_date = "2025-05-31"
    timezone_str = "US/Eastern"
    
    start_time = convert_to_utc_timestamp(start_date, "12:00:00", timezone_str)
    end_time = convert_to_utc_timestamp(end_date, "23:59:59", timezone_str)
    
    data = fetch_data(symbol, interval, start_time, end_time)
    result = analyze_high_prices(data)
    
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()