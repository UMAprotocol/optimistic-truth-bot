import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    
    Args:
        symbol (str): The symbol to fetch data for, e.g., 'ETHUSDT'.
        interval (str): The interval of the klines data, e.g., '1h'.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        dict: The JSON response containing the price data.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
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
            raise

def convert_to_utc_timestamp(date_str, time_str, timezone_str):
    """
    Converts a date and time string from a specified timezone to UTC timestamp in milliseconds.
    
    Args:
        date_str (str): Date in 'YYYY-MM-DD' format.
        time_str (str): Time in 'HH:MM' format.
        timezone_str (str): Timezone string, e.g., 'US/Eastern'.
    
    Returns:
        int: UTC timestamp in milliseconds.
    """
    local_tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_datetime = local_tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    return int(utc_datetime.timestamp() * 1000)

def main():
    # Specific date and time for the Ethereum price check
    date_str = "2025-06-19"
    time_str = "22:00"
    timezone_str = "US/Eastern"
    symbol = "ETHUSDT"
    interval = "1h"
    
    # Convert the specified time to UTC timestamp in milliseconds
    start_time = convert_to_utc_timestamp(date_str, time_str, timezone_str)
    end_time = start_time + 3600000  # 1 hour later
    
    # Fetch the price data
    try:
        data = fetch_price_data(symbol, interval, start_time, end_time)
        if data and len(data) > 0:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            if close_price >= open_price:
                print("recommendation: p2")  # Up
            else:
                print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # Unknown/50-50 if no data
    except Exception as e:
        print(f"Failed to fetch or process data: {e}")
        print("recommendation: p3")  # Unknown/50-50 on error

if __name__ == "__main__":
    main()