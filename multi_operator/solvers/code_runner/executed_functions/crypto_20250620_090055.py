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

def get_eth_price_data(date_str, hour, minute, timezone_str):
    """
    Fetches the ETH/USDT 1-hour candle data from Binance for a specific time.
    """
    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    target_time_local = tz.localize(datetime.strptime(f"{date_str} {hour:02d}:{minute:02d}:00", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(pytz.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000) - 3600000  # Subtract 1 hour to get the start of the candle
    end_time_ms = start_time_ms + 3600000  # 1 hour later

    # URLs for API requests
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    # Try the proxy endpoint first
    try:
        response = requests.get(f"{proxy_url}?symbol=ETHUSDT&interval=1h&limit=1&startTime={start_time_ms}&endTime={end_time_ms}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return open_price, close_price
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")

    # Fall back to primary endpoint if proxy fails
    try:
        response = requests.get(f"{primary_url}?symbol=ETHUSDT&interval=1h&limit=1&startTime={start_time_ms}&endTime={end_time_ms}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return open_price, close_price
    except Exception as e:
        logger.error(f"Primary endpoint failed: {str(e)}")
        raise

def main():
    """
    Main function to determine if the ETH price went up or down at the specified time.
    """
    # Specific date and time for the query
    date_str = "2025-06-20"
    hour = 4  # 4 AM ET
    minute = 0
    timezone_str = "US/Eastern"

    try:
        open_price, close_price = get_eth_price_data(date_str, hour, minute, timezone_str)
        logger.info(f"Open price: {open_price}, Close price: {close_price}")

        if close_price >= open_price:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logger.error(f"Error retrieving or processing data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    main()