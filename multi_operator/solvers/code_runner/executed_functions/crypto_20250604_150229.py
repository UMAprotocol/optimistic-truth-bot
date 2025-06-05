import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000  # Adjust based on the maximum allowed by the API
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy failed with error: {e}, falling back to primary API.")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def convert_to_utc_timestamp(date_str, time_str='00:00:00', timezone_str='US/Eastern'):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    local_tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    local_dt = local_tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def check_new_high(symbol, start_date, end_date):
    """
    Checks if there is a new all-time high within the given date range.
    """
    # Convert dates to UTC timestamps
    start_timestamp = convert_to_utc_timestamp(start_date)
    end_timestamp = convert_to_utc_timestamp(end_date, time_str='23:59:59')

    # Fetch historical data
    historical_data = fetch_data(symbol, '1m', start_timestamp, end_timestamp)
    if not historical_data:
        return "p4"  # Unable to resolve due to data fetch failure

    # Find the highest price in the given range
    highest_price = max([float(candle[2]) for candle in historical_data])

    # Fetch all previous data to compare
    previous_data = fetch_data(symbol, '1m', 0, start_timestamp - 1)
    if not previous_data:
        return "p4"  # Unable to resolve due to data fetch failure

    # Find the previous all-time high
    previous_highest_price = max([float(candle[2]) for candle in previous_data])

    # Determine if a new all-time high was reached
    if highest_price > previous_highest_price:
        return "p2"  # Yes, new all-time high
    else:
        return "p1"  # No new all-time high

def main():
    """
    Main function to determine if XRP reached a new all-time high in May 2025.
    """
    result = check_new_high("XRPUSDT", "2025-05-01", "2025-05-31")
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()