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

def get_ethusdt_price_change(date_str, hour, minute, timezone_str):
    """
    Fetches the percentage change for the ETHUSDT pair for the 1-hour candle starting at the specified time.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format
        minute: Minute
        timezone_str: Timezone string

    Returns:
        Percentage change as float
    """
    logger.info(f"Fetching ETHUSDT price change for {date_str} at {hour}:{minute} {timezone_str}")
    
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
        raise

    # Binance API endpoint
    api_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "ETHUSDT",
        "interval": "1h",
        "limit": 1,
        "startTime": start_time_ms,
        "endTime": start_time_ms + 3600000  # plus 1 hour
    }

    try:
        response = requests.get(api_url, params=params)
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
        raise Exception(f"Failed to fetch ETHUSDT price data: {e}")

def main():
    """
    Main function to handle the Ethereum price change query.
    """
    # Specific query details
    date_str = "2025-06-11"
    hour = 7
    minute = 0
    timezone_str = "US/Eastern"

    try:
        price_change_percent = get_ethusdt_price_change(date_str, hour, minute, timezone_str)
        
        # Determine resolution based on price change
        if price_change_percent >= 0:
            recommendation = "p2"  # Up
        else:
            recommendation = "p1"  # Down
        
        print(f"recommendation: {recommendation}")
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        print("recommendation: p3")  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    main()