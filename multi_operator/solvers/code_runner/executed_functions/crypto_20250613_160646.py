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

def fetch_price_from_binance(symbol, interval, start_time, end_time):
    """
    Fetches cryptocurrency price data from Binance using the proxy endpoint with a fallback to the primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            raise

def convert_to_utc_timestamp(date_str, hour, minute, timezone_str):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
    local_dt = tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    # Specific date and time for the query
    date_str = "2025-06-13"
    hour = 12  # Noon
    minute = 0
    timezone_str = "US/Eastern"
    symbol = "ETHUSDT"
    threshold_price = 2400.0

    # Convert the specified time to UTC timestamp
    start_time = convert_to_utc_timestamp(date_str, hour, minute, timezone_str)
    end_time = start_time + 60000  # 1 minute later

    try:
        # Fetch the close price from Binance
        close_price = fetch_price_from_binance(symbol, "1m", start_time, end_time)
        print(f"Close price for {symbol} at {date_str} {hour}:{minute} {timezone_str} is {close_price}")

        # Determine the resolution based on the fetched price
        if close_price > threshold_price:
            print("recommendation: p2")  # Yes
        else:
            print("recommendation: p1")  # No
    except Exception as e:
        print(f"Failed to fetch data: {str(e)}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()