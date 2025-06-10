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
        symbol (str): The symbol to fetch data for.
        interval (str): The interval of the klines data.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        float: The closing price of the candle.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary API.")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data[0][4])  # Closing price
        except Exception as e:
            print(f"Primary API failed with error: {e}")
            raise

def convert_to_utc_timestamp(date_str, hour, timezone_str):
    """
    Converts a date string with specific hour and timezone to UTC timestamp in milliseconds.
    
    Args:
        date_str (str): Date in 'YYYY-MM-DD' format.
        hour (int): Hour of the day (24-hour format).
        timezone_str (str): Timezone string.
    
    Returns:
        int: UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(timezone_str)
    naive_dt = datetime.strptime(date_str + f" {hour}:00:00", "%Y-%m-%d %H:%M:%S")
    local_dt = tz.localize(naive_dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    # Specific event details
    date_str = "2025-05-30"
    hour = 6  # 6 AM ET
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"
    interval = "1h"
    
    # Convert event time to UTC timestamp
    start_time = convert_to_utc_timestamp(date_str, hour, timezone_str)
    end_time = start_time + 3600000  # 1 hour later in milliseconds
    
    # Fetch the closing price for the specified candle
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