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

def get_btc_price_at_specific_time(date_str, hour=2, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the BTC/USDT 1-hour candle open and close price on Binance at a specific time on a given date.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format (default: 2 AM)
        minute: Minute (default: 0)
        timezone_str: Timezone string (default: "US/Eastern")

    Returns:
        Tuple of (open_price, close_price) as floats
    """
    logger.info(f"Fetching BTC/USDT price for {date_str} at {hour}:{minute} {timezone_str}")
    
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
        "symbol": "BTCUSDT",
        "interval": "1h",
        "limit": 1,
        "startTime": start_time_ms,
        "endTime": start_time_ms + 3600000  # plus 1 hour
    }

    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return (open_price, close_price)
        else:
            logger.error("No data returned from Binance API.")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the open and close prices.

    Args:
        open_price: Opening price of the BTC/USDT 1-hour candle
        close_price: Closing price of the BTC/USDT 1-hour candle

    Returns:
        Market resolution as a string
    """
    if close_price >= open_price:
        return "p2"  # Market resolves to "Up"
    else:
        return "p1"  # Market resolves to "Down"

def main():
    """
    Main function to handle the market resolution based on BTC/USDT prices on Binance.
    """
    # Date and time for the market resolution
    date_str = "2025-06-18"
    hour = 2  # 2 AM ET

    # Fetch prices
    prices = get_btc_price_at_specific_time(date_str, hour)
    if prices:
        open_price, close_price = prices
        # Resolve the market
        resolution = resolve_market(open_price, close_price)
        print(f"recommendation: {resolution}")
    else:
        print("recommendation: p4")  # Unable to resolve due to data fetch failure

if __name__ == "__main__":
    main()