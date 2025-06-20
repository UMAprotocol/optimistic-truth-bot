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

def get_binance_data(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try proxy endpoint first
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Proxy failed with error {e}, trying primary endpoint.")
        try:
            # Fallback to primary endpoint
            response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price
        except Exception as e:
            print(f"Primary endpoint also failed with error {e}")
            raise

def convert_to_utc_timestamp(date_str, hour=12, minute=0, timezone_str="US/Eastern"):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
    local_dt = tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    """
    Main function to determine if the price of SOLUSDT went up or down between two specific times.
    """
    symbol = "SOLUSDT"
    date1 = "2025-06-09"
    date2 = "2025-06-10"
    hour = 12  # Noon
    minute = 0
    timezone_str = "US/Eastern"

    try:
        start_time1 = convert_to_utc_timestamp(date1, hour, minute, timezone_str)
        end_time1 = start_time1 + 60000  # 1 minute later in milliseconds

        start_time2 = convert_to_utc_timestamp(date2, hour, minute, timezone_str)
        end_time2 = start_time2 + 60000  # 1 minute later in milliseconds

        close_price1 = get_binance_data(symbol, start_time1, end_time1)
        close_price2 = get_binance_data(symbol, start_time2, end_time2)

        if close_price1 < close_price2:
            print("recommendation: p2")  # Up
        elif close_price1 > close_price2:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        print(f"Failed to resolve due to error: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()