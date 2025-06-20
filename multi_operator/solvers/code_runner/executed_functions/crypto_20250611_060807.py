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
    Fetches the percentage change for the BTCUSDT pair on Binance for the specified time.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format
        minute: Minute
        timezone_str: Timezone string

    Returns:
        A string indicating the resolution based on the price change.
    """
    try:
        # Convert the target time to UTC timestamp
        tz = pytz.timezone(timezone_str)
        time_str = f"{hour:02d}:{minute:02d}:00"
        target_time_local = tz.localize(
            datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        )
        target_time_utc = target_time_local.astimezone(timezone.utc)
        start_time_ms = int(target_time_utc.timestamp() * 1000)

        # Binance API endpoint for 1-hour candle data
        api_url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "limit": 1,
            "startTime": start_time_ms - 3600000,  # 1 hour before to get the correct candle
            "endTime": start_time_ms
        }

        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            price_change_percentage = ((close_price - open_price) / open_price) * 100

            if price_change_percentage >= 0:
                return "recommendation: p2"  # Up
            else:
                return "recommendation: p1"  # Down
        else:
            return "recommendation: p3"  # Unknown/50-50 if no data

    except Exception as e:
        logger.error(f"Failed to fetch or process data: {e}")
        return "recommendation: p3"  # Default to unknown/50-50 on error

def main():
    """
    Main function to determine the price change of BTCUSDT on Binance for June 11, 2025, 1 AM ET.
    """
    result = get_btc_price_change("2025-06-11", 1, 0, "US/Eastern")
    print(result)

if __name__ == "__main__":
    main()