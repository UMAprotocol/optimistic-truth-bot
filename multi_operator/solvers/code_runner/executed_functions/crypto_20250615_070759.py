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
        "limit": 1
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            close_price = float(data[0][4])
            return close_price
    except requests.RequestException as e:
        logger.error(f"Failed to fetch data from Binance: {e}")
        return None

def convert_to_utc_timestamp(date_str, hour, timezone_str):
    """
    Converts a date and time in a specific timezone to a UTC timestamp.

    Args:
        date_str: Date in 'YYYY-MM-DD' format
        hour: Hour of the day (24-hour format)
        timezone_str: Timezone string (e.g., 'US/Eastern')

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
    date_str = "2025-06-15"
    hour = 2  # 2 AM ET
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"

    # Convert the specified date and time to UTC timestamp
    start_time = convert_to_utc_timestamp(date_str, hour, timezone_str)

    # Fetch the closing price of the 1-hour candle starting at the specified time
    close_price = get_binance_price(symbol, start_time)

    if close_price is not None:
        # Fetch the closing price of the previous 1-hour candle
        previous_close_price = get_binance_price(symbol, start_time - 3600000)

        if previous_close_price is not None:
            # Calculate the percentage change
            percentage_change = ((close_price - previous_close_price) / previous_close_price) * 100

            # Determine the market resolution based on the percentage change
            if percentage_change >= 0:
                print("recommendation: p2")  # Up
            else:
                print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # Unknown/50-50 due to data fetch error
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data fetch error

if __name__ == "__main__":
    main()