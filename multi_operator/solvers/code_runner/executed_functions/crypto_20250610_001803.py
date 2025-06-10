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

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    
    Args:
        symbol (str): The symbol to fetch data for.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        float: The lowest price in the given time frame or None if no data.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Max limit
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            # Find the lowest price in the returned data
            return min(float(candle[3]) for candle in data)  # Index 3 is the low price
    except Exception as e:
        print(f"Proxy failed, trying primary API: {e}")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return min(float(candle[3]) for candle in data)
        except Exception as e:
            print(f"Both proxy and primary API requests failed: {e}")
            return None

def convert_to_utc_timestamp(date_str, time_str, timezone_str):
    """
    Converts a date and time string from a specified timezone to UTC timestamp in milliseconds.
    
    Args:
        date_str (str): Date in 'YYYY-MM-DD' format.
        time_str (str): Time in 'HH:MM' format.
        timezone_str (str): Timezone string.
    
    Returns:
        int: UTC timestamp in milliseconds.
    """
    local_tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_datetime = local_tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    return int(utc_datetime.timestamp() * 1000)

def main():
    # Define the symbol and the time period to check
    symbol = "HYPEUSDC"
    start_date = "2025-05-07"
    end_date = "2025-05-31"
    start_time = "16:00"
    end_time = "23:59"
    timezone_str = "US/Eastern"

    # Convert start and end times to UTC timestamps
    start_timestamp = convert_to_utc_timestamp(start_date, start_time, timezone_str)
    end_timestamp = convert_to_utc_timestamp(end_date, end_time, timezone_str)

    # Fetch the lowest price in the given period
    lowest_price = fetch_price_data(symbol, start_timestamp, end_timestamp)

    # Determine the resolution based on the lowest price
    if lowest_price is not None and lowest_price <= 18.0:
        print("recommendation: p2")  # Yes, the price dipped to $18 or lower
    else:
        print("recommendation: p1")  # No, the price did not dip to $18 or lower

if __name__ == "__main__":
    main()