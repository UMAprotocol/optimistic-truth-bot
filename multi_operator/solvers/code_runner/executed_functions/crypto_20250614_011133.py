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
    Fetches the percentage change for the BTC/USDT pair on Binance for the specified 1-hour candle.

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
        target_time_local = tz.localize(datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S"))
        target_time_utc = target_time_local.astimezone(pytz.utc)
        start_time_ms = int(target_time_utc.timestamp() * 1000)
        end_time_ms = start_time_ms + 3600000  # 1 hour later

        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "startTime": start_time_ms,
            "endTime": end_time_ms,
            "limit": 1
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            percentage_change = ((close_price - open_price) / open_price) * 100
            return percentage_change
    except Exception as e:
        logger.error(f"Failed to fetch or parse data: {e}")
        return None

def main():
    """
    Main function to determine if the BTC/USDT price went up or down on June 13, 2025, at 8 PM ET.
    """
    percentage_change = get_btc_price_change("2025-06-13", 20, 0, "US/Eastern")

    if percentage_change is None:
        print("recommendation: p3")  # Unknown/50-50 if data cannot be fetched
    elif percentage_change >= 0:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

if __name__ == "__main__":
    main()