import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_eth_price(date_str, hour, minute):
    """
    Fetches the ETH/USDT price for a specific hour and minute on a given date.
    Args:
        date_str (str): Date in 'YYYY-MM-DD' format.
        hour (int): Hour of the day (24-hour format).
        minute (int): Minute of the hour.
    Returns:
        tuple: (open_price, close_price)
    """
    # Convert local time to UTC
    local_time = datetime.strptime(f"{date_str} {hour}:{minute}", "%Y-%m-%d %H:%M")
    eastern = pytz.timezone('US/Eastern')
    local_dt = eastern.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)

    # Calculate timestamps in milliseconds
    start_timestamp = int(utc_dt.timestamp() * 1000)
    end_timestamp = start_timestamp + 3600000  # 1 hour later

    # Construct the URL and parameters for the API request
    params = {
        'symbol': 'ETHUSDT',
        'interval': '1h',
        'startTime': start_timestamp,
        'endTime': end_timestamp,
        'limit': 1
    }

    # Try fetching data from the proxy endpoint first
    try:
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params)
        response.raise_for_status()
        data = response.json()
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    except Exception as e:
        print(f"Proxy failed, trying primary endpoint: {e}")
        # Fallback to the primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params)
            response.raise_for_status()
            data = response.json()
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return open_price, close_price
        except Exception as e:
            print(f"Both proxy and primary endpoints failed: {e}")
            raise

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the open and close prices.
    Args:
        open_price (float): Opening price of ETH/USDT.
        close_price (float): Closing price of ETH/USDT.
    Returns:
        str: Market resolution recommendation.
    """
    if close_price >= open_price:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

def main():
    # Example date and time for the market resolution
    date_str = "2025-06-19"
    hour = 8
    minute = 0

    try:
        open_price, close_price = fetch_eth_price(date_str, hour, minute)
        resolution = resolve_market(open_price, close_price)
        print(resolution)
    except Exception as e:
        print(f"Failed to resolve market: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()