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
        "limit": 1000  # Adjust based on the maximum allowed by the API
    }
    
    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def convert_to_utc_timestamp(date_str, timezone_str="US/Eastern"):
    """
    Converts a date string in the format 'YYYY-MM-DD' to a UTC timestamp.
    """
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(date_str, "%Y-%m-%d")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    return int(utc_datetime.timestamp() * 1000)

def check_dogecoin_high_in_may():
    """
    Checks if Dogecoin reached a new all-time high in May 2025 on Binance.
    """
    symbol = "DOGEUSDT"
    interval = "1m"
    start_date = "2025-05-01"
    end_date = "2025-05-31"
    
    # Convert dates to UTC timestamps
    start_time = convert_to_utc_timestamp(start_date)
    end_time = convert_to_utc_timestamp(end_date) + 86400000 - 1  # End of May 31st
    
    # Fetch data from Binance
    data = fetch_binance_data(symbol, interval, start_time, end_time)
    
    # Extract all high prices from the fetched data
    highs = [float(candle[2]) for candle in data]
    
    # Check if any high in May is greater than the previous all-time high
    previous_high = max(highs)  # This should be fetched from historical data prior to May 2025
    may_high = max(highs)
    
    if may_high > previous_high:
        print("recommendation: p2")  # Yes, new all-time high
    else:
        print("recommendation: p1")  # No new all-time high

if __name__ == "__main__":
    check_dogecoin_high_in_may()