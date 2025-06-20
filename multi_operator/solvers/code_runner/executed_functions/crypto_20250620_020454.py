import requests
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_eth_price(date_str, hour, minute, timezone_str):
    """
    Fetches the ETH/USDT price for a specific hour and minute on a given date from Binance.
    
    Args:
        date_str (str): Date in YYYY-MM-DD format.
        hour (int): Hour of the day (24-hour format).
        minute (int): Minute of the hour.
        timezone_str (str): Timezone string (e.g., "US/Eastern").
    
    Returns:
        tuple: (open_price, close_price) if successful, None otherwise.
    """
    try:
        # Convert local time to UTC
        tz = pytz.timezone(timezone_str)
        local_dt = tz.localize(datetime.strptime(f"{date_str} {hour}:{minute}", "%Y-%m-%d %H:%M"))
        utc_dt = local_dt.astimezone(pytz.utc)
        start_time = int(utc_dt.timestamp() * 1000)  # Convert to milliseconds
        end_time = start_time + 3600000  # 1 hour later

        # First try the proxy endpoint
        proxy_url = f"{PROXY_BINANCE_API}?symbol=ETHUSDT&interval=1h&limit=1&startTime={start_time}&endTime={end_time}"
        response = requests.get(proxy_url)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return (open_price, close_price)
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary endpoint.")
        # Fallback to primary endpoint
        primary_url = f"{PRIMARY_BINANCE_API}/klines?symbol=ETHUSDT&interval=1h&limit=1&startTime={start_time}&endTime={end_time}"
        response = requests.get(primary_url)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return (open_price, close_price)
    return None

def main():
    # Specific date and time for the query
    date_str = "2025-06-19"
    hour = 21  # 9 PM ET
    minute = 0
    timezone_str = "US/Eastern"

    # Fetch the price data
    price_data = fetch_eth_price(date_str, hour, minute, timezone_str)
    if price_data:
        open_price, close_price = price_data
        # Determine the resolution based on the open and close prices
        if close_price >= open_price:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data fetch failure

if __name__ == "__main__":
    main()