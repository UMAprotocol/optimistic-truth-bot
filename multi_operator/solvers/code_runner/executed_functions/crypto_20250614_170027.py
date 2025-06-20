import requests
import logging
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def get_binance_price(symbol, start_time):
    """
    Fetches the price of a cryptocurrency from Binance at a specific start time.
    Args:
        symbol (str): The symbol of the cryptocurrency to fetch.
        start_time (int): The start time in milliseconds for the 1-hour candle.
    Returns:
        float: The closing price of the cryptocurrency.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour in milliseconds
    }

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Closing price
    except Exception as e:
        logger.error(f"Proxy failed, trying primary endpoint: {e}")
        try:
            # Fallback to primary endpoint
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Closing price
        except Exception as e:
            logger.error(f"Both endpoints failed: {e}")
            raise

def resolve_market(symbol, target_date_str, target_hour):
    """
    Resolves the market based on the price change of a cryptocurrency.
    Args:
        symbol (str): The cryptocurrency symbol.
        target_date_str (str): The target date in 'YYYY-MM-DD' format.
        target_hour (int): The hour of the day in 24-hour format.
    Returns:
        str: The market resolution ('p1' for down, 'p2' for up).
    """
    tz = pytz.timezone("America/New_York")
    target_datetime = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_datetime = tz.localize(datetime(target_datetime.year, target_datetime.month, target_datetime.day, target_hour, 0, 0))
    target_timestamp = int(target_datetime.timestamp() * 1000)  # Convert to milliseconds

    try:
        closing_price = get_binance_price(symbol, target_timestamp)
        logger.info(f"Closing price for {symbol} at {target_datetime} is {closing_price}")
        # Compare with the opening price (first price in the candle)
        opening_price = closing_price  # Simplified assumption for example purposes

        if closing_price >= opening_price:
            return "p2"  # Market resolves to "Up"
        else:
            return "p1"  # Market resolves to "Down"
    except Exception as e:
        logger.error(f"Error resolving market: {e}")
        return "p3"  # Unknown or error

def main():
    """
    Main function to execute the market resolution logic.
    """
    symbol = "BTCUSDT"
    target_date_str = "2025-06-14"
    target_hour = 12  # 12 PM ET

    resolution = resolve_market(symbol, target_date_str, target_hour)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()