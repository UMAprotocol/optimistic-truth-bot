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
    Fetches the percentage change for the ETHUSDT pair from Binance for a specific hour candle.

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
        dt = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
        dt_local = tz.localize(dt)
        dt_utc = dt_local.astimezone(pytz.utc)

        start_time = int(dt_utc.timestamp() * 1000)
        end_time = start_time + 3600000  # 1 hour later

        proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
        primary_url = "https://api.binance.com/api/v3/klines"

        params = {
            "symbol": "ETHUSDT",
            "interval": "1h",
            "startTime": start_time,
            "endTime": end_time
        }

        try:
            response = requests.get(f"{proxy_url}", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error(f"Proxy failed, falling back to primary. Error: {e}")
            response = requests.get(f"{primary_url}", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            change_percent = ((close_price - open_price) / open_price) * 100
            return change_percent
    except Exception as e:
        logger.error(f"Failed to fetch or parse data: {e}")
        return None

def main():
    """
    Main function to determine if the ETH price went up or down.
    """
    date_str = "2025-06-11"
    hour = 1
    minute = 0
    timezone_str = "US/Eastern"

    change = get_eth_price_change(date_str, hour, minute, timezone_str)
    if change is None:
        print("recommendation: p3")  # Unknown or error
    elif change >= 0:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

if __name__ == "__main__":
    main()