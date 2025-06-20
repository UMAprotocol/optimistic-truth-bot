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

def get_eth_price_change(date_str, hour=12, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the percentage change for the ETH/USDT pair on Binance for the specified time.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format (default: 12)
        minute: Minute (default: 0)
        timezone_str: Timezone string (default: "US/Eastern")

    Returns:
        Percentage change as float or None if data cannot be retrieved.
    """
    logger.info(f"Fetching ETH/USDT price change for {date_str} at {hour}:{minute} {timezone_str}")
    
    # Convert the target time to UTC timestamp
    try:
        tz = pytz.timezone(timezone_str)
        time_str = f"{hour:02d}:{minute:02d}:00"
        target_time_local = tz.localize(
            datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        )
        target_time_utc = target_time_local.astimezone(timezone.utc)
        start_time_ms = int(target_time_utc.timestamp() * 1000)
        
        logger.debug(f"Converted local time to UTC timestamp: {start_time_ms}")
    except Exception as e:
        logger.error(f"Error converting time: {e}")
        return None

    # Binance API endpoint
    api_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "ETHUSDT",
        "interval": "1h",
        "limit": 1,
        "startTime": start_time_ms - 3600000,  # 1 hour before to get the full candle
        "endTime": start_time_ms
    }

    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            price_change_percent = ((close_price - open_price) / open_price) * 100
            logger.info(f"Successfully retrieved price change: {price_change_percent}%")
            return price_change_percent
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
    
    return None

def main():
    """
    Main function to determine if the ETH/USDT price went up or down at the specified time.
    """
    # Specific date and time for the query
    date_str = "2025-06-17"
    hour = 12  # 12 PM ET
    minute = 0
    timezone_str = "US/Eastern"

    try:
        price_change_percent = get_eth_price_change(date_str, hour, minute, timezone_str)
        
        if price_change_percent is not None:
            if price_change_percent >= 0:
                print("recommendation: p2")  # Up
            else:
                print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # Unknown/50-50 due to data retrieval failure
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()