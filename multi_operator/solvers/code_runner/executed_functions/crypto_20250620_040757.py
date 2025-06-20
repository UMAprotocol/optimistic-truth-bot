import requests
import logging
from datetime import datetime
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

def get_solana_price(date_str, hour, minute, timezone_str):
    """
    Fetches the SOL/USDT price for a specific hour candle on Binance.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format
        minute: Minute
        timezone_str: Timezone string

    Returns:
        Tuple of (open_price, close_price)
    """
    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    target_time_local = tz.localize(datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(pytz.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)

    # Binance API endpoint
    api_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "SOLUSDT",
        "interval": "1h",
        "limit": 1,
        "startTime": start_time_ms,
        "endTime": start_time_ms + 3600000  # 1 hour later
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    except Exception as e:
        logger.error(f"Failed to fetch SOL/USDT price data: {e}")
        raise

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the open and close prices.

    Args:
        open_price: Opening price of the SOL/USDT pair
        close_price: Closing price of the SOL/USDT pair

    Returns:
        Market resolution as a string
    """
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to handle the resolution of the Solana market.
    """
    try:
        # Date and time for the event
        date_str = "2025-06-19"
        hour = 23  # 11 PM ET
        minute = 0
        timezone_str = "US/Eastern"

        # Fetch prices
        open_price, close_price = get_solana_price(date_str, hour, minute, timezone_str)

        # Resolve the market
        resolution = resolve_market(open_price, close_price)

        # Output the recommendation
        print(f"recommendation: {resolution}")
    except Exception as e:
        logger.error(f"Error during market resolution: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()