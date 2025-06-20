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

def get_eth_price_at_specific_time(date_str, hour=21, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the 1-hour candle close price for ETHUSDT on Binance at a specific time on a given date.
    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format (default: 21 for 9 PM ET)
        minute: Minute (default: 0)
        timezone_str: Timezone string (default: "US/Eastern")
    Returns:
        Close price as float
    """
    logger.info(f"Fetching ETHUSDT price for {date_str} at {hour}:{minute} {timezone_str}")
    
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
            close_price = float(data[0][4])
            logger.info(f"Successfully retrieved price: {close_price}")
            return close_price
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise Exception(f"Failed to fetch ETHUSDT price data: {e}")

def main():
    """
    Main function to handle the Ethereum price query for June 11, 2025, 9 PM ET.
    """
    query_date = "2025-06-11"
    query_hour = 21  # 9 PM ET
    query_minute = 0
    query_timezone = "US/Eastern"
    
    logger.info(f"Processing Ethereum price query for {query_date} at {query_hour}:{query_minute} {query_timezone}")
    
    try:
        # Get price for the specified date and time
        price_at_start = get_eth_price_at_specific_time(query_date, query_hour, query_minute, query_timezone)
        price_at_end = get_eth_price_at_specific_time(query_date, query_hour + 1, query_minute, query_timezone)
        
        # Determine if the price went up or down
        if price_at_end >= price_at_start:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
            
    except Exception as e:
        logger.error(f"Error processing Ethereum price query: {e}")
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()