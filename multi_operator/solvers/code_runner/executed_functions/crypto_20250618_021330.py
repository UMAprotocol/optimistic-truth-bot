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
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_solana_price(date_str, hour, minute, timezone_str):
    """
    Fetches the SOL/USDT price from Binance at a specific time.
    
    Args:
        date_str (str): Date in YYYY-MM-DD format.
        hour (int): Hour in 24-hour format.
        minute (int): Minute.
        timezone_str (str): Timezone string.
    
    Returns:
        tuple: (open_price, close_price) or None if an error occurs.
    """
    try:
        tz = pytz.timezone(timezone_str)
        naive_datetime = datetime.strptime(f"{date_str} {hour}:{minute}", "%Y-%m-%d %H:%M")
        local_datetime = tz.localize(naive_datetime)
        utc_datetime = local_datetime.astimezone(pytz.utc)
        start_time = int(utc_datetime.timestamp() * 1000)  # Convert to milliseconds

        params = {
            "symbol": "SOLUSDT",
            "interval": "1h",
            "startTime": start_time,
            "endTime": start_time + 3600000  # 1 hour later
        }
        response = requests.get("https://api.binance.com/api/v3/klines", params=params)
        response.raise_for_status()
        data = response.json()[0]
        open_price = float(data[1])
        close_price = float(data[4])
        return open_price, close_price
    except Exception as e:
        logger.error(f"Failed to fetch SOL/USDT price: {e}")
        return None

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the open and close prices.
    
    Args:
        open_price (float): Opening price of SOL/USDT.
        close_price (float): Closing price of SOL/USDT.
    
    Returns:
        str: 'p1' if down, 'p2' if up, 'p3' if unknown.
    """
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to process the market resolution.
    """
    # Specific date and time for the market resolution
    date_str = "2025-06-17"
    hour = 21  # 9 PM ET
    minute = 0
    timezone_str = "US/Eastern"

    # Fetch the SOL/USDT price at the specified time
    price_data = fetch_solana_price(date_str, hour, minute, timezone_str)
    if price_data:
        open_price, close_price = price_data
        # Resolve the market based on the fetched prices
        resolution = resolve_market(open_price, close_price)
        print(f"recommendation: {resolution}")
    else:
        print("recommendation: p3")  # Unknown or error

if __name__ == "__main__":
    main()