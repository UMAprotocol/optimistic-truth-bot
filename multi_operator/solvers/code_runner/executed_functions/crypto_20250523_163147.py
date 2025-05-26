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

def get_close_price_at_specific_time(date_str, hour=12, minute=0, timezone_str="US/Eastern", symbol="HYPEUSDC"):
    """
    Fetches the 1-minute candle close price for a cryptocurrency pair on Hyperliquid
    at a specific time on a given date.
    """
    logger.info(f"Fetching {symbol} price for {date_str} at {hour}:{minute} {timezone_str}")
    
    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    time_str = f"{hour:02d}:{minute:02d}:00"
    target_time_local = tz.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    
    # Hyperliquid API endpoint
    api_url = "https://app.hyperliquid.xyz/api/v1/public/getklines"
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
        if data and data['data']:
            close_price = float(data['data'][0][4])  # Close price is the fifth element in the list
            logger.info(f"Successfully retrieved price: {close_price}")
            return close_price
        else:
            logger.error("No data returned from API")
            return None
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        return None

def main():
    """
    Main function to handle cryptocurrency price queries.
    """
    # Extracted from the question
    date1 = "2025-05-22"
    date2 = "2025-05-23"
    symbol = "HYPEUSDC"
    timezone_str = "US/Eastern"
    
    # Get prices for both dates at 12:00 noon
    price1 = get_close_price_at_specific_time(date1, 12, 0, timezone_str, symbol)
    price2 = get_close_price_at_specific_time(date2, 12, 0, timezone_str, symbol)
    
    # Determine the resolution based on the prices
    if price1 is not None and price2 is not None:
        if price1 < price2:
            print("recommendation: p2")  # Up
        elif price1 > price2:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    else:
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()