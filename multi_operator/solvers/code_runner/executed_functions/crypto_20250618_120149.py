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

def fetch_eth_price(date_str, hour, minute, timezone_str):
    """
    Fetches the ETH/USDT price data for a specific hour and minute on a given date.
    Args:
        date_str (str): Date in YYYY-MM-DD format.
        hour (int): Hour of the day (24-hour format).
        minute (int): Minute of the hour.
        timezone_str (str): Timezone string.
    Returns:
        tuple: (open_price, close_price) if successful, None otherwise.
    """
    # Convert local time to UTC
    local = pytz.timezone(timezone_str)
    naive = datetime.strptime(f"{date_str} {hour}:{minute}", "%Y-%m-%d %H:%M")
    local_dt = local.localize(naive, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)

    # Calculate the milliseconds for the API call
    start_time = int(utc_dt.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Prepare API parameters
    params = {
        "symbol": "ETHUSDT",
        "interval": "1h",
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }

    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return (open_price, close_price)
    except Exception as e:
        print(f"Proxy failed, error: {e}, trying primary endpoint.")
        try:
            # Fallback to the primary endpoint if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                open_price = float(data[0][1])
                close_price = float(data[0][4])
                return (open_price, close_price)
        except Exception as e:
            print(f"Primary endpoint also failed, error: {e}")

    return None

def main():
    # Specific date and time for the market resolution
    date_str = "2025-06-18"
    hour = 7
    minute = 0
    timezone_str = "US/Eastern"

    # Fetch the price data
    result = fetch_eth_price(date_str, hour, minute, timezone_str)
    if result:
        open_price, close_price = result
        if close_price >= open_price:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data fetch failure

if __name__ == "__main__":
    main()