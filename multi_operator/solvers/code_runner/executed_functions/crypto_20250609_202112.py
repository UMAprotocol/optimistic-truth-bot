import requests
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price(symbol, start_time, end_time):
    """
    Fetches the closing price of a cryptocurrency from Binance using both the proxy and primary API endpoints.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            return float(data[0][4])  # Close price
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data and len(data) > 0:
                return float(data[0][4])  # Close price
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            raise

def convert_to_utc_timestamp(date_str, time_str, timezone_str):
    """
    Converts a date and time string from a specified timezone to a UTC timestamp.
    """
    tz = pytz.timezone(timezone_str)
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    dt_local = tz.localize(dt)
    dt_utc = dt_local.astimezone(pytz.utc)
    return int(dt_utc.timestamp() * 1000)  # Convert to milliseconds

def main():
    # Define the symbols and times for the query
    symbol = "ETHBTC"
    start_date = "2025-05-01"
    end_date = "2025-05-31"
    start_time = "12:00"
    end_time = "23:59"
    timezone_str = "US/Eastern"

    # Convert times to UTC timestamps
    start_timestamp = convert_to_utc_timestamp(start_date, start_time, timezone_str)
    end_timestamp = convert_to_utc_timestamp(end_date, end_time, timezone_str)

    # Fetch prices
    try:
        start_price = fetch_price(symbol, start_timestamp, start_timestamp + 60000)  # 1 minute range
        end_price = fetch_price(symbol, end_timestamp, end_timestamp + 60000)  # 1 minute range

        # Determine the resolution based on the prices
        if start_price < end_price:
            print("recommendation: p2")  # Up
        elif start_price > end_price:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        print(f"Failed to fetch prices: {str(e)}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()