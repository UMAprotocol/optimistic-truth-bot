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
    Fetches data from Binance API with a fallback to a proxy if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000  # Adjust based on the maximum results needed per call
    }
    
    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary endpoint.")
        # Fallback to the primary endpoint if proxy fails
        response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def convert_to_utc_timestamp(date_str, timezone_str="UTC"):
    """
    Converts a date string to a UTC timestamp.
    """
    local_tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    local_datetime = local_tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    return int(utc_datetime.timestamp() * 1000)

def check_xrp_all_time_high():
    """
    Checks if XRP reached a new all-time high in May 2025.
    """
    symbol = "XRPUSDT"
    interval = "1m"
    start_date = "2025-05-01 00:00:00"
    end_date = "2025-05-31 23:59:59"
    timezone_str = "US/Eastern"

    start_time = convert_to_utc_timestamp(start_date, timezone_str)
    end_time = convert_to_utc_timestamp(end_date, timezone_str)

    # Fetch historical data for the entire month of May 2025
    data = fetch_binance_data(symbol, interval, start_time, end_time)

    # Extract all high prices from the data
    high_prices = [float(candle[2]) for candle in data]

    # Determine if a new all-time high was reached
    if not high_prices:
        return "p4"  # Unable to determine due to lack of data

    current_max_high = max(high_prices)
    historical_max_high = 3.40  # This should be dynamically fetched or stored from previous data

    if current_max_high > historical_max_high:
        return "p2"  # Yes, a new all-time high was reached
    else:
        return "p1"  # No new all-time high was reached

def main():
    result = check_xrp_all_time_high()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()