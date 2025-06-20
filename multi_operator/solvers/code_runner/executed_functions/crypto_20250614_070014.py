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
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def get_eth_price_change(date_str, hour, minute, timezone_str):
    """
    Fetches the percentage change for the ETH/USDT pair from Binance for a specific 1-hour candle.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format
        minute: Minute
        timezone_str: Timezone string

    Returns:
        Percentage change as float or None if data cannot be fetched.
    """
    try:
        tz = pytz.timezone(timezone_str)
        dt = datetime.strptime(f"{date_str} {hour}:{minute}", "%Y-%m-%d %H:%M")
        dt_local = tz.localize(dt)
        dt_utc = dt_local.astimezone(pytz.utc)

        start_time = int(dt_utc.timestamp() * 1000)  # Convert to milliseconds
        end_time = start_time + 3600000  # 1 hour later

        # URLs for Binance API
        primary_url = "https://api.binance.com/api/v3/klines"
        proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

        # Parameters for API request
        params = {
            "symbol": "ETHUSDT",
            "interval": "1h",
            "startTime": start_time,
            "endTime": end_time,
            "limit": 1
        }

        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data:
                open_price = float(data[0][1])
                close_price = float(data[0][4])
                return ((close_price - open_price) / open_price) * 100
        else:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(primary_url, params=params)
            response.raise_for_status()
            data = response.json()
            if data:
                open_price = float(data[0][1])
                close_price = float(data[0][4])
                return ((close_price - open_price) / open_price) * 100

    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        return None

def main():
    """
    Main function to determine if the ETH/USDT price went up or down.
    """
    date_str = "2025-06-14"
    hour = 2
    minute = 0
    timezone_str = "US/Eastern"

    change = get_eth_price_change(date_str, hour, minute, timezone_str)
    if change is not None:
        if change >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50

if __name__ == "__main__":
    main()