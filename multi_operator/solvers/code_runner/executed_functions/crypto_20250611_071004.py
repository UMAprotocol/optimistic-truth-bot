import requests
import logging
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_eth_price_change(date_str, hour, minute, timezone_str):
    """
    Fetches the percentage change for the ETHUSDT pair for the 1-hour candle starting at the specified time.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format
        minute: Minute
        timezone_str: Timezone string

    Returns:
        Percentage change as float or None if data cannot be fetched.
    """
    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    target_time_local = tz.localize(datetime.strptime(f"{date_str} {hour:02d}:{minute:02d}:00", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later

    # URLs setup
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    # Try proxy endpoint first
    try:
        response = requests.get(proxy_url, params={
            "symbol": "ETHUSDT",
            "interval": "1h",
            "limit": 1,
            "startTime": start_time_ms,
            "endTime": end_time_ms
        }, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return 100 * (close_price - open_price) / open_price
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}, falling back to primary endpoint")

    # Fallback to primary endpoint
    try:
        response = requests.get(primary_url, params={
            "symbol": "ETHUSDT",
            "interval": "1h",
            "limit": 1,
            "startTime": start_time_ms,
            "endTime": end_time_ms
        }, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return 100 * (close_price - open_price) / open_price
    except Exception as e:
        logging.error(f"Primary endpoint also failed: {e}")
        return None

def main():
    """
    Main function to determine if the ETH price went up or down at a specific time.
    """
    # Specific date and time for the query
    date_str = "2025-06-11"
    hour = 2  # 2 AM ET
    minute = 0
    timezone_str = "US/Eastern"

    price_change = get_eth_price_change(date_str, hour, minute, timezone_str)
    if price_change is not None:
        if price_change >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data fetch failure

if __name__ == "__main__":
    main()