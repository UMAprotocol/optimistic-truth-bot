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

def get_binance_price(symbol, start_time):
    """
    Fetches the closing price of a cryptocurrency from Binance for a specific 1-hour candle.

    Args:
        symbol: Cryptocurrency symbol (e.g., 'BTCUSDT')
        start_time: Start time of the 1-hour candle in milliseconds

    Returns:
        Closing price as float or None if an error occurs
    """
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": "1h",
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            close_price = float(data[0][4])  # Closing price of the candle
            return close_price
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from Binance: {e}")
        return None

def convert_to_utc(year, month, day, hour, minute, timezone_str):
    """
    Converts a given date and time to UTC.

    Args:
        year, month, day, hour, minute: Date and time components
        timezone_str: Timezone string (e.g., 'US/Eastern')

    Returns:
        UTC datetime object
    """
    tz = pytz.timezone(timezone_str)
    local_time = tz.localize(datetime(year, month, day, hour, minute))
    utc_time = local_time.astimezone(pytz.utc)
    return utc_time

def main():
    # Define the event details
    year, month, day = 2025, 6, 16
    hour, minute = 17, 0  # 5 PM ET
    timezone_str = 'US/Eastern'
    symbol = 'BTCUSDT'

    # Convert event time to UTC
    utc_time = convert_to_utc(year, month, day, hour, minute, timezone_str)
    start_time_ms = int(utc_time.timestamp() * 1000)

    # Fetch the closing price from Binance
    closing_price = get_binance_price(symbol, start_time_ms)
    if closing_price is None:
        print("recommendation: p4")  # Unable to resolve
        return

    # Fetch the opening price from Binance 1 hour earlier
    opening_price = get_binance_price(symbol, start_time_ms - 3600000)
    if opening_price is None:
        print("recommendation: p4")  # Unable to resolve
        return

    # Determine the market resolution based on price change
    if closing_price >= opening_price:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

if __name__ == "__main__":
    main()