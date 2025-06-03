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

def get_btc_price_change(date_str, hour=6, timezone_str="US/Eastern"):
    """
    Fetches the percentage change for the BTC/USDT pair on Binance for the specified hour candle.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format (default: 6 AM)
        timezone_str: Timezone string (default: "US/Eastern")

    Returns:
        Percentage change as float
    """
    logger.info(f"Fetching BTC/USDT price change for {date_str} at {hour} {timezone_str}")
    
    # Convert the target time to UTC timestamp
    try:
        tz = pytz.timezone(timezone_str)
        target_time_local = tz.localize(datetime.strptime(f"{date_str} {hour}:00:00", "%Y-%m-%d %H:%M:%S"))
        target_time_utc = target_time_local.astimezone(timezone.utc)
        start_time_ms = int(target_time_utc.timestamp() * 1000)
        end_time_ms = start_time_ms + 3600000  # plus 1 hour
    except Exception as e:
        logger.error(f"Error converting time: {e}")
        raise

    # Binance API endpoint
    api_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "BTCUSDT",
        "interval": "1h",
        "limit": 1,
        "startTime": start_time_ms,
        "endTime": end_time_ms
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            price_change_percent = ((close_price - open_price) / open_price) * 100
            logger.info(f"Open price: {open_price}, Close price: {close_price}, Change: {price_change_percent}%")
            return price_change_percent
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise

def main():
    """
    Main function to determine if the BTC/USDT price went up or down on June 3, 2025 at 6 AM ET.
    """
    try:
        price_change = get_btc_price_change("2025-06-03")
        if price_change >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logger.error(f"Failed to fetch or process data: {e}")
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()