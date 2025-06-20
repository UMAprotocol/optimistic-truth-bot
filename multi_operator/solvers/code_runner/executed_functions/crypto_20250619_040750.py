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

def get_eth_price_at_specific_time(date_str, hour=23, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the 1-hour candle open and close price for ETH/USDT on Binance
    at a specific time on a given date.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format (default: 23)
        minute: Minute (default: 0)
        timezone_str: Timezone string (default: "US/Eastern")

    Returns:
        Tuple of (open price, close price)
    """
    logger.info(f"Fetching ETH/USDT price for {date_str} at {hour}:{minute} {timezone_str}")
    
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
            logger.info(f"Successfully retrieved open price: {open_price} and close price: {close_price}")
            return (open_price, close_price)
        else:
            logger.error("No data returned from API")
            raise Exception("No data available")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise

def main():
    """
    Main function to handle the Ethereum price query for June 18, 2025, 11 PM ET.
    """
    try:
        # Fetch prices
        open_price, close_price = get_eth_price_at_specific_time("2025-06-18", 23, 0, "US/Eastern")
        
        # Determine resolution based on open and close prices
        if close_price >= open_price:
            recommendation = "p2"  # Up
        else:
            recommendation = "p1"  # Down
        
        # Output the recommendation
        print(f"recommendation: {recommendation}")
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        # Default to p3 (unknown/50-50) in case of any errors
        print("recommendation: p3")

if __name__ == "__main__":
    main()