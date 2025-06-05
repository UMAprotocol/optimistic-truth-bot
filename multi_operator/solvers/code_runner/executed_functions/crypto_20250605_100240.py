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

def get_btc_price_change(date_str, hour=5, timezone_str="US/Eastern"):
    """
    Fetches the percentage change for the BTC/USDT pair on Binance for the specified hour.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format (default: 5 AM)
        timezone_str: Timezone string (default: "US/Eastern")

    Returns:
        Percentage change as float or None if data cannot be retrieved.
    """
    logger.info(f"Fetching BTC/USDT price change for {date_str} at {hour} {timezone_str}")
    
    # Convert the target time to UTC timestamp
    try:
        tz = pytz.timezone(timezone_str)
        target_time_local = tz.localize(datetime.strptime(f"{date_str} {hour}:00:00", "%Y-%m-%d %H:%M:%S"))
        target_time_utc = target_time_local.astimezone(timezone.utc)
        start_time_ms = int(target_time_utc.timestamp() * 1000) - 3600000  # 1 hour candle start time
        end_time_ms = start_time_ms + 3600000  # 1 hour candle end time
    except Exception as e:
        logger.error(f"Error converting time: {e}")
        return None

    # Binance API endpoint for candlestick data
    api_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "BTCUSDT",
        "interval": "1h",
        "startTime": start_time_ms,
        "endTime": end_time_ms
    }

    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            price_change_percent = ((close_price - open_price) / open_price) * 100
            return price_change_percent
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
    except (IndexError, ValueError) as e:
        logger.error(f"Error processing API response: {e}")

    return None

def main():
    """
    Main function to determine if the BTC/USDT price went up or down on June 5, 2025, at 5 AM ET.
    """
    date_str = "2025-06-05"
    hour = 5
    timezone_str = "US/Eastern"

    price_change_percent = get_btc_price_change(date_str, hour, timezone_str)

    if price_change_percent is None:
        print("recommendation: p3")  # Unknown/50-50 if data cannot be retrieved
    elif price_change_percent >= 0:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

if __name__ == "__main__":
    main()