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

def get_solana_price_data(date_str, hour, minute, timezone_str):
    """
    Fetches the SOL/USDT 1-hour candle data from Binance for a specific time.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format
        minute: Minute
        timezone_str: Timezone string

    Returns:
        Tuple of (open_price, close_price)
    """
    try:
        tz = pytz.timezone(timezone_str)
        time_str = f"{hour:02d}:{minute:02d}:00"
        target_time_local = tz.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S"))
        target_time_utc = target_time_local.astimezone(timezone.utc)
        start_time_ms = int(target_time_utc.timestamp() * 1000) - 3600000  # Subtract 1 hour to get the start of the candle

        api_url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": "SOLUSDT",
            "interval": "1h",
            "limit": 1,
            "startTime": start_time_ms,
            "endTime": start_time_ms + 3600000  # 1 hour later
        }

        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return (open_price, close_price)
        else:
            logger.error("No data returned from Binance API.")
            return None
    except Exception as e:
        logger.error(f"Failed to fetch price data: {e}")
        return None

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the open and close prices.

    Args:
        open_price: Opening price of the SOL/USDT pair
        close_price: Closing price of the SOL/USDT pair

    Returns:
        Market resolution as a string.
    """
    if close_price >= open_price:
        return "p2"  # Market resolves to "Up"
    else:
        return "p1"  # Market resolves to "Down"

def main():
    """
    Main function to handle the resolution of the Solana market.
    """
    # Date and time for the event
    date_str = "2025-06-19"
    hour = 7
    minute = 0
    timezone_str = "US/Eastern"

    # Fetch the price data
    price_data = get_solana_price_data(date_str, hour, minute, timezone_str)

    if price_data:
        open_price, close_price = price_data
        # Resolve the market
        resolution = resolve_market(open_price, close_price)
        print(f"recommendation: {resolution}")
    else:
        print("recommendation: p4")  # Unable to resolve due to data fetch failure

if __name__ == "__main__":
    main()