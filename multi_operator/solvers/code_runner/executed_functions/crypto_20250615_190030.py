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
        Percentage change as float or None if data cannot be retrieved.
    """
    try:
        tz = pytz.timezone(timezone_str)
        dt = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
        dt = tz.localize(dt)
        dt_utc = dt.astimezone(pytz.utc)
        start_time = int(dt_utc.timestamp() * 1000)  # Convert to milliseconds
        end_time = start_time + 3600000  # 1 hour later

        # URLs for API requests
        proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
        primary_url = "https://api.binance.com/api/v3/klines"

        # First try the proxy endpoint
        try:
            response = requests.get(f"{proxy_url}?symbol=ETHUSDT&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                open_price = float(data[0][1])
                close_price = float(data[0][4])
                return ((close_price - open_price) / open_price) * 100
        except Exception as e:
            logger.error(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")

        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol=ETHUSDT&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
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
    # Specific date and time for the query
    date_str = "2025-06-15"
    hour = 14  # 2 PM ET
    minute = 0
    timezone_str = "US/Eastern"

    price_change = get_eth_price_change(date_str, hour, minute, timezone_str)
    if price_change is not None:
        if price_change >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50

if __name__ == "__main__":
    main()