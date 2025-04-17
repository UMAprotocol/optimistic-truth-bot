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
    tz = pytz.timezone(timezone_str)
    time_str = f"{hour:02d}:{minute:02d}:00"
    target_time_local = tz.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    
    # Binance API endpoint
    api_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time_ms,
        "endTime": start_time_ms + 60000  # plus 1 minute
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        logger.info(f"Successfully retrieved price: {close_price}")
        return close_price
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        raise

def main():
    """
    Main function to handle cryptocurrency price queries.
    """
    # Dates and times for the query
    date1 = "2025-04-15"
    date2 = "2025-04-16"
    symbol = "BTCUSDT"
    timezone_str = "US/Eastern"

    try:
        # Get prices for both dates at 12:00 ET
        price1 = get_close_price_at_specific_time(date1, 12, 0, timezone_str, symbol)
        price2 = get_close_price_at_specific_time(date2, 12, 0, timezone_str, symbol)

        # Determine the resolution based on the prices
        if price2 > price1:
            recommendation = "recommendation: p2"  # Up
        elif price2 < price1:
            recommendation = "recommendation: p1"  # Down
        else:
            recommendation = "recommendation: p3"  # 50-50

        print(recommendation)
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()