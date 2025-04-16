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

def get_close_price_at_specific_time(date_str, hour=12, minute=0, timezone_str="US/Eastern", symbol="BTCUSDT"):
    """
    Fetches the 1-minute candle close price for a cryptocurrency pair on Binance
    at a specific time on a given date.
    """
    logger.info(f"Fetching {symbol} price for {date_str} at {hour}:{minute} {timezone_str}")
    
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

    api_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time_ms,
        "endTime": start_time_ms + 60_000,  # plus 1 minute
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data:
            close_price = float(data[0][4])
            logger.info(f"Successfully retrieved price: {close_price}")
            return close_price
    except Exception as e:
        logger.error(f"Failed to fetch {symbol} price data: {e}")
        raise

def main():
    """
    Main function to handle cryptocurrency price queries.
    """
    try:
        # Get prices for both dates
        price1 = get_close_price_at_specific_time("2025-04-15", 12, 0, "US/Eastern", "BTCUSDT")
        price2 = get_close_price_at_specific_time("2025-04-16", 12, 0, "US/Eastern", "BTCUSDT")
        
        # Determine resolution
        if price1 < price2:
            resolution = "p2"  # Up
        elif price1 > price2:
            resolution = "p1"  # Down
        else:
            resolution = "p3"  # 50-50
        
        # Output the recommendation
        print(f"recommendation: {resolution}")
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        print("recommendation: p4")

if __name__ == "__main__":
    main()