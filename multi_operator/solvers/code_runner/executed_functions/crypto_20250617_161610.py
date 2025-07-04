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
        symbol (str): The symbol to fetch data for (e.g., 'BTCUSDT').
        interval (str): The interval of the klines data (e.g., '1h').
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        float: The closing price of the symbol at the specified time.
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
        data = response.json()
        return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy API failed, error: {e}. Falling back to primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data[0][4])  # Closing price
        except Exception as e:
            print(f"Primary API also failed, error: {e}.")
            raise

def convert_to_utc_timestamp(date_str, time_str, timezone_str):
    """
    Converts local time to UTC timestamp in milliseconds.
    
    Args:
        date_str (str): Date in 'YYYY-MM-DD' format.
        time_str (str): Time in 'HH:MM' format.
        timezone_str (str): Timezone string (e.g., 'US/Eastern').
    
    Returns:
        int: UTC timestamp in milliseconds.
    """
    local_tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_dt = local_tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    # Specific date and time for the query
    date_str = "2025-06-17"
    time_str = "11:00"
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"
    interval = "1h"
    
    # Convert the specified time to UTC timestamp
    start_time = convert_to_utc_timestamp(date_str, time_str, timezone_str)
    end_time = start_time + 3600000  # 1 hour later in milliseconds
    
    # Fetch the closing price for the specified time
    try:
        closing_price = fetch_price_data(symbol, interval, start_time, end_time)
        print(f"Closing price for {symbol} at {date_str} {time_str} {timezone_str} is {closing_price}")
    except Exception as e:
        print(f"Failed to fetch data: {e}")

if __name__ == "__main__":
    main()