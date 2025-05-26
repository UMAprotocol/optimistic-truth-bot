import requests
import os
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Proxy failed, error: {e}, trying primary endpoint.")
        # Fallback to the primary endpoint
        try:
            response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data[0][4])  # Close price
        except Exception as e:
            print(f"Primary endpoint also failed, error: {e}")
            raise

def convert_to_utc_timestamp(date_str, hour=12, minute=0, tz_str="US/Eastern"):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(tz_str)
    local_dt = tz.localize(datetime.strptime(date_str, "%Y-%m-%d"))
    local_dt = local_dt.replace(hour=hour, minute=minute)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    # Define the symbols and dates based on the ancillary data provided
    symbol = "ETHBTC"
    date1_str = "2025-05-22"
    date2_str = "2025-05-23"
    
    # Convert dates to UTC timestamps
    start_time1 = convert_to_utc_timestamp(date1_str)
    end_time1 = start_time1 + 60000  # 1 minute later in milliseconds
    start_time2 = convert_to_utc_timestamp(date2_str)
    end_time2 = start_time2 + 60000  # 1 minute later in milliseconds
    
    try:
        # Fetch close prices for both dates
        close_price1 = fetch_binance_data(symbol, start_time1, end_time1)
        close_price2 = fetch_binance_data(symbol, start_time2, end_time2)
        
        # Determine the resolution based on the close prices
        if close_price1 < close_price2:
            print("recommendation: p2")  # Up
        elif close_price1 > close_price2:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        print(f"Failed to resolve due to error: {e}")
        print("recommendation: p4")  # Unknown or error

if __name__ == "__main__":
    main()