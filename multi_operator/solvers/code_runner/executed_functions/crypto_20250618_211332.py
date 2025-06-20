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

def get_solana_price_data(target_datetime_utc):
    """
    Fetches the SOL/USDT 1-hour candle data from Binance for a specific UTC datetime.

    Args:
        target_datetime_utc: The target datetime in UTC as a datetime object.

    Returns:
        A tuple (open_price, close_price) if successful, None otherwise.
    """
    api_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "SOLUSDT",
        "interval": "1h",
        "startTime": int(target_datetime_utc.timestamp() * 1000),
        "endTime": int((target_datetime_utc + timedelta(hours=1)).timestamp() * 1000)
    }

    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return (open_price, close_price)
        else:
            logger.error("No data returned from Binance API.")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from Binance API: {e}")
        return None

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the open and close prices.

    Args:
        open_price: The opening price of the SOL/USDT pair.
        close_price: The closing price of the SOL/USDT pair.

    Returns:
        A string indicating the market resolution.
    """
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to handle the resolution of the Solana Up or Down market.
    """
    # Define the target datetime in Eastern Time
    target_datetime_et = datetime(2025, 6, 18, 16, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    # Convert to UTC
    target_datetime_utc = target_datetime_et.astimezone(pytz.utc)

    # Fetch the price data
    price_data = get_solana_price_data(target_datetime_utc)
    if price_data:
        open_price, close_price = price_data
        # Resolve the market
        resolution = resolve_market(open_price, close_price)
        print(f"recommendation: {resolution}")
    else:
        print("recommendation: p3")  # Unknown/50-50 if data cannot be fetched

if __name__ == "__main__":
    main()