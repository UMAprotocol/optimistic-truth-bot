import requests
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price(symbol, interval, start_time, end_time):
    """
    Fetches the price data from Binance API with a fallback to a proxy server.
    
    Args:
        symbol (str): The symbol to fetch, e.g., 'BTCUSDT'
        interval (str): The interval of the klines/candles, e.g., '1m'
        start_time (int): Start time in milliseconds
        end_time (int): End time in milliseconds
    
    Returns:
        float: The closing price of the candle
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching from the proxy API first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Proxy API failed: {e}, falling back to primary API")
        # Fallback to the primary API if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Close price

def convert_to_utc_timestamp(date_str, timezone_str):
    """
    Converts a date string in a specific timezone to a UTC timestamp in milliseconds.
    
    Args:
        date_str (str): Date string in 'YYYY-MM-DD HH:MM' format
        timezone_str (str): Timezone string, e.g., 'US/Eastern'
    
    Returns:
        int: UTC timestamp in milliseconds
    """
    local_tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    local_dt = local_tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    # Define the symbol and the interval
    symbol = "BTCUSDT"
    interval = "1m"
    
    # Define the start and end times
    start_time_str = "2025-05-01 00:00"
    end_time_str = "2025-05-31 23:59"
    timezone_str = "US/Eastern"
    
    # Convert times to UTC timestamps
    start_time = convert_to_utc_timestamp(start_time_str, timezone_str)
    end_time = convert_to_utc_timestamp(end_time_str, timezone_str)
    
    # Fetch prices
    start_price = fetch_price(symbol, interval, start_time, start_time + 60000)  # 1 minute range
    end_price = fetch_price(symbol, interval, end_time, end_time + 60000)  # 1 minute range
    
    # Determine the resolution
    if start_price < end_price:
        print("recommendation: p2")  # Up
    elif start_price > end_price:
        print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # 50-50

if __name__ == "__main__":
    main()