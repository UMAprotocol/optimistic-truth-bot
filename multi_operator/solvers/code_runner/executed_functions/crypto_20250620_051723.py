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

def get_sol_price_at_specific_time(date_str, hour=0, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the 1-hour candle open and close price for SOL/USDT on Binance
    at a specific time on a given date.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format (default: 0)
        minute: Minute (default: 0)
        timezone_str: Timezone string (default: "US/Eastern")

    Returns:
        Tuple of (open price, close price)
    """
    logger.info(f"Fetching SOL/USDT price for {date_str} at {hour}:{minute} {timezone_str}")
    
    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    time_str = f"{hour:02d}:{minute:02d}:00"
    target_time_local = tz.localize(
        datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    )
    target_time_utc = target_time_local.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    
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
            return (open_price, close_price)
        else:
            logger.error("No data returned from Binance API")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the open and close prices.

    Args:
        open_price: Opening price of the candle
        close_price: Closing price of the candle

    Returns:
        Market resolution as a string
    """
    if close_price >= open_price:
        return "p2"  # Market resolves to "Up"
    else:
        return "p1"  # Market resolves to "Down"

def main():
    """
    Main function to handle the resolution of the Solana Up or Down market.
    """
    # Date and time for the event
    event_date = "2025-06-20"
    event_hour = 0  # 12 AM ET

    # Fetch the open and close prices
    prices = get_sol_price_at_specific_time(event_date, event_hour)
    if prices:
        open_price, close_price = prices
        # Resolve the market based on the prices
        resolution = resolve_market(open_price, close_price)
        print(f"recommendation: {resolution}")
    else:
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()