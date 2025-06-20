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

def get_btc_price_change(date_str, hour, minute, timezone_str):
    """
    Fetches the percentage change for the BTC/USDT pair on Binance for the specified hour candle.

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

        start_time = int(dt_utc.timestamp() * 1000)  # Convert to milliseconds
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
        data = response.json()

        if data and len(data) > 0:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            change_percent = ((close_price - open_price) / open_price) * 100
            return change_percent
        else:
            return None
    except Exception as e:
        logger.error(f"Failed to fetch BTC price data: {e}")
        return None

def main():
    """
    Main function to determine if the BTC price went up or down at the specified time.
    """
    # Specific date and time for the query
    date_str = "2025-06-10"
    hour = 23  # 11 PM
    minute = 0
    timezone_str = "US/Eastern"

    change_percent = get_btc_price_change(date_str, hour, minute, timezone_str)

    if change_percent is None:
        print("recommendation: p3")  # Unknown/50-50 if data cannot be fetched
    elif change_percent >= 0:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

if __name__ == "__main__":
    main()