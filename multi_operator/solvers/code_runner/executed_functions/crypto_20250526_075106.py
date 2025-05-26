import requests
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API URLs
PRIMARY_BINANCE_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data using the proxy URL first
        response = requests.get(PROXY_BINANCE_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary API endpoint.")
        try:
            # Fallback to the primary API endpoint if proxy fails
            response = requests.get(PRIMARY_BINANCE_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data[0][4])  # Close price
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            raise

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
    # Define the dates, times, and timezone
    date1 = "2025-05-25"
    date2 = "2025-05-26"
    time_str = "12:00:00"
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"

    # Convert times to UTC timestamps
    start_time1 = convert_to_utc_timestamp(date1, time_str, timezone_str)
    end_time1 = start_time1 + 60000  # 1 minute later in milliseconds
    start_time2 = convert_to_utc_timestamp(date2, time_str, timezone_str)
    end_time2 = start_time2 + 60000  # 1 minute later in milliseconds

    try:
        # Fetch close prices for both dates
        close_price1 = fetch_binance_data(symbol, "1m", start_time1, end_time1)
        close_price2 = fetch_binance_data(symbol, "1m", start_time2, end_time2)

        # Determine the market resolution
        if close_price1 < close_price2:
            print("recommendation: p2")  # Up
        elif close_price1 > close_price2:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        print(f"Failed to resolve market due to error: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()