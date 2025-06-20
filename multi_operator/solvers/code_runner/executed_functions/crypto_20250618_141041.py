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

def get_eth_price(date_str, hour, minute, timezone_str):
    """
    Fetches the ETH/USDT price for a specific hour and minute on a given date from Binance.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format
        minute: Minute
        timezone_str: Timezone string

    Returns:
        Tuple of (open_price, close_price)
    """
    logger.info(f"Fetching ETH/USDT price for {date_str} at {hour}:{minute} {timezone_str}")
    
    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    time_str = f"{hour:02d}:{minute:02d}:00"
    target_time_local = tz.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)

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
            return (open_price, close_price)
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from Binance: {e}")
        raise

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the open and close prices.

    Args:
        open_price: Opening price of the ETH/USDT pair
        close_price: Closing price of the ETH/USDT pair

    Returns:
        Market resolution as a string
    """
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to handle the resolution of the Ethereum price market.
    """
    try:
        # Date and time for the event
        date_str = "2025-06-18"
        hour = 9
        minute = 0
        timezone_str = "US/Eastern"

        # Fetch prices
        open_price, close_price = get_eth_price(date_str, hour, minute, timezone_str)

        # Resolve the market
        resolution = resolve_market(open_price, close_price)

        # Output the recommendation
        print(f"recommendation: {resolution}")
        
    except Exception as e:
        logger.error(f"Error processing the market resolution: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()