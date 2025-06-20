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
    Fetches the closing price of a cryptocurrency pair from Binance for a specific 1-hour candle.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        start_time: Start time of the 1-hour candle in milliseconds since epoch

    Returns:
        Closing price as float or None if an error occurs
    """
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": "1h",
        "startTime": start_time,
        "limit": 1
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            close_price = float(data[0][4])
            return close_price
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from Binance: {e}")
        return None

def convert_to_utc_timestamp(date_str, hour, timezone_str):
    """
    Converts a date and time in a specific timezone to a UTC timestamp.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format
        timezone_str: Timezone string (e.g., "US/Eastern")

    Returns:
        UTC timestamp in milliseconds
    """
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(date_str + f" {hour}:00:00", "%Y-%m-%d %H:%M:%S")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    return int(utc_datetime.timestamp() * 1000)

def main():
    # Specific date and time for the market resolution
    date_str = "2025-06-16"
    hour = 17  # 5 PM ET
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"

    # Convert the specified date and time to UTC timestamp
    start_time = convert_to_utc_timestamp(date_str, hour, timezone_str)

    # Fetch the closing price for the specified 1-hour candle
    close_price_start = get_binance_price(symbol, start_time)
    close_price_end = get_binance_price(symbol, start_time + 3600000)  # 1 hour later

    if close_price_start is None or close_price_end is None:
        print("recommendation: p4")  # Unable to resolve due to data fetch error
        return

    # Determine the market resolution based on the price change
    if close_price_end >= close_price_start:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

if __name__ == "__main__":
    main()