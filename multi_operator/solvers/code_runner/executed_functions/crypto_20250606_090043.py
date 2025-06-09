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

def convert_to_utc(year, month, day, hour, minute, tz_name):
    """
    Converts local time to UTC timestamp in milliseconds.
    
    Args:
        year (int): Year of the date.
        month (int): Month of the date.
        day (int): Day of the date.
        hour (int): Hour of the time.
        minute (int): Minute of the time.
        tz_name (str): Timezone name (e.g., 'US/Eastern').
    
    Returns:
        int: UTC timestamp in milliseconds.
    """
    local_tz = pytz.timezone(tz_name)
    local_time = local_tz.localize(datetime(year, month, day, hour, minute))
    utc_time = local_time.astimezone(pytz.utc)
    return int(utc_time.timestamp() * 1000)

def main():
    # Specific date and time for the query
    year, month, day = 2025, 6, 6
    hour, minute = 4, 0  # 4 AM ET
    tz_name = 'US/Eastern'
    symbol = 'BTCUSDT'
    interval = '1h'
    
    # Convert the specified time to UTC milliseconds
    start_time = convert_to_utc(year, month, day, hour, minute, tz_name)
    end_time = start_time + 3600000  # Plus one hour
    
    # Fetch the closing price for the specified time
    try:
        closing_price_start = fetch_price_data(symbol, interval, start_time, start_time + 60000)  # Start of the hour
        closing_price_end = fetch_price_data(symbol, interval, end_time - 60000, end_time)  # End of the hour
        
        # Determine if the price went up or down
        if closing_price_end >= closing_price_start:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        print(f"Failed to fetch data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if data fetch fails

if __name__ == "__main__":
    main()