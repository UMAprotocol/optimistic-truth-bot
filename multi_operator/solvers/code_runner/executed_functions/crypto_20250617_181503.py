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

def get_sol_price_at_specific_time(date_str, hour=13, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the 1-hour candle open and close price for SOL/USDT on Binance
    at a specific time on a given date.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format (default: 13 for 1 PM ET)
        minute: Minute (default: 0)
        timezone_str: Timezone string (default: "US/Eastern")

    Returns:
        Tuple of (open price, close price) as floats
    """
    logger.info(f"Fetching SOL/USDT price for {date_str} at {hour}:{minute} {timezone_str}")
    
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
        "symbol": "SOLUSDT",
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
            logger.info(f"Successfully retrieved open price: {open_price} and close price: {close_price}")
            return (open_price, close_price)
        else:
            logger.error("No data returned from Binance API")
            raise Exception("No data available")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise Exception(f"Failed to fetch SOL/USDT price data: {e}")

def main():
    """
    Main function to handle the resolution of the market based on SOL/USDT prices.
    """
    date_str = "2025-06-17"  # Date of interest
    logger.info(f"Processing price data for {date_str}")
    
    try:
        open_price, close_price = get_sol_price_at_specific_time(date_str)
        
        if close_price >= open_price:
            print("recommendation: p2")  # Market resolves to "Up"
        else:
            print("recommendation: p1")  # Market resolves to "Down"
        
    except Exception as e:
        logger.error(f"Error processing price data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()