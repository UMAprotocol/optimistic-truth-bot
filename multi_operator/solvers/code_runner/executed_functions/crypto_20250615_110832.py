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
    Fetches the closing price of a specific 1-hour candle from Binance API.

    Args:
        symbol (str): The symbol to fetch, e.g., 'BTCUSDT'.
        start_time (int): The start time of the candle in milliseconds.

    Returns:
        float: The closing price of the candle.
    """
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": "1h",
        "startTime": start_time,
        "limit": 1
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            close_price = float(data[0][4])
            return close_price
        else:
            logger.error("No data returned from Binance API.")
            return None
    except requests.RequestException as e:
        logger.error(f"Error fetching data from Binance API: {e}")
        return None

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance.

    Returns:
        str: The resolution of the market ('p1' for Down, 'p2' for Up, 'p3' for unknown).
    """
    symbol = "BTCUSDT"
    target_date = datetime(2025, 6, 15, 6, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    target_date_utc = target_date.astimezone(pytz.utc)
    start_time_ms = int(target_date_utc.timestamp() * 1000)

    # Fetch the closing price of the 1-hour candle starting at the target time
    close_price_start = get_binance_price(symbol, start_time_ms)
    if close_price_start is None:
        return "p3"  # Unknown if no data

    # Fetch the closing price of the previous 1-hour candle
    previous_candle_start_ms = start_time_ms - 3600000  # 1 hour in milliseconds
    close_price_previous = get_binance_price(symbol, previous_candle_start_ms)
    if close_price_previous is None:
        return "p3"  # Unknown if no data

    # Determine if the price went up or down
    if close_price_start >= close_price_previous:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    resolution = resolve_market()
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()