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

def get_binance_data(symbol, start_time):
    """
    Fetches the 1-hour candle data for a cryptocurrency pair on Binance at a specific start time.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        start_time: Start time for the 1-hour candle in milliseconds

    Returns:
        JSON response containing candle data
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
        return response.json()
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(primary_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_date_str, target_hour):
    """
    Determines the market resolution based on the price change of a cryptocurrency.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        target_date_str: Target date in "YYYY-MM-DD" format
        target_hour: Target hour in 24-hour format

    Returns:
        Market resolution as a string
    """
    # Convert target time to UTC timestamp
    tz = pytz.timezone("US/Eastern")
    target_datetime = datetime.strptime(f"{target_date_str} {target_hour}:00:00", "%Y-%m-%d %H:%M:%S")
    target_datetime = tz.localize(target_datetime).astimezone(pytz.utc)
    start_time_ms = int(target_datetime.timestamp() * 1000)

    # Fetch data
    data = get_binance_data(symbol, start_time_ms)
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change_percentage = ((close_price - open_price) / open_price) * 100

        # Determine resolution based on price change
        if price_change_percentage >= 0:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data

def main():
    """
    Main function to handle the resolution of the Bitcoin Up or Down market.
    """
    symbol = "BTCUSDT"
    target_date_str = "2025-05-29"
    target_hour = 13  # 1 PM ET

    try:
        resolution = resolve_market(symbol, target_date_str, target_hour)
        print(f"recommendation: {resolution}")
    except Exception as e:
        logger.error(f"Error resolving market: {e}")
        print("recommendation: p3")  # Default to unknown/50-50 in case of errors

if __name__ == "__main__":
    main()