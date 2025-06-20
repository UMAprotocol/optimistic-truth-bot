import requests
import logging
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def get_btc_price(date_str, hour, minute, timezone_str):
    """
    Fetches the BTC/USDT price for a specific hour and minute on a given date from Binance.

    Args:
        date_str: Date in YYYY-MM-DD format.
        hour: Hour in 24-hour format.
        minute: Minute.
        timezone_str: Timezone string.

    Returns:
        A tuple (open_price, close_price) as floats.
    """
    try:
        tz = pytz.timezone(timezone_str)
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        dt = tz.localize(datetime(dt.year, dt.month, dt.day, hour, minute, 0))
        dt_utc = dt.astimezone(pytz.utc)

        # Convert datetime to milliseconds since epoch
        start_time = int(dt_utc.timestamp() * 1000)
        end_time = start_time + 3600000  # 1 hour later

        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "startTime": start_time,
            "endTime": end_time,
            "limit": 1
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()[0]
        open_price = float(data[1])
        close_price = float(data[4])

        return open_price, close_price

    except Exception as e:
        logger.error(f"Failed to fetch BTC price data: {e}")
        raise

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the open and close prices.

    Args:
        open_price: Opening price of BTC/USDT.
        close_price: Closing price of BTC/USDT.

    Returns:
        'p1' if the price went down, 'p2' if the price went up, 'p3' if unknown.
    """
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to resolve the market based on BTC/USDT prices on Binance.
    """
    try:
        # The specific date and time for the market resolution
        date_str = "2025-06-18"
        hour = 9  # 9 AM ET
        minute = 0
        timezone_str = "US/Eastern"

        open_price, close_price = get_btc_price(date_str, hour, minute, timezone_str)
        resolution = resolve_market(open_price, close_price)
        print(f"recommendation: {resolution}")

    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()