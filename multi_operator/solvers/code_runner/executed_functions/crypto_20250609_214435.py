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

def fetch_price(symbol, start_time, end_time):
    """
    Fetches the closing price of a cryptocurrency from Binance using the provided symbol and time range.
    Args:
        symbol (str): The symbol for the cryptocurrency pair (e.g., 'SOLUSDT').
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    Returns:
        float: The closing price of the cryptocurrency.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to the primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            return float(data[0][4])  # Closing price

    raise Exception("Failed to fetch data from both endpoints.")

def convert_to_utc_timestamp(date_str, time_str, timezone_str):
    """
    Converts a date and time string from a specified timezone to a UTC timestamp.
    Args:
        date_str (str): Date in 'YYYY-MM-DD' format.
        time_str (str): Time in 'HH:MM' format.
        timezone_str (str): Timezone string.
    Returns:
        int: UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(timezone_str)
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_dt = tz.localize(dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    # Define the dates, times, and timezone
    start_date = "2025-05-01"
    end_date = "2025-05-31"
    time_str = "12:00"
    timezone_str = "US/Eastern"
    symbol = "SOLUSDT"

    # Convert times to UTC timestamps
    start_time = convert_to_utc_timestamp(start_date, time_str, timezone_str)
    end_time = convert_to_utc_timestamp(end_date, "23:59", timezone_str)

    # Fetch prices
    start_price = fetch_price(symbol, start_time, start_time + 60000)  # 1 minute range
    end_price = fetch_price(symbol, end_time, end_time + 60000)  # 1 minute range

    # Determine the resolution based on the prices
    if start_price < end_price:
        print("recommendation: p2")  # Up
    elif start_price > end_price:
        print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # 50-50

if __name__ == "__main__":
    main()