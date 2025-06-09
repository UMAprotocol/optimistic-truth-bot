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

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def get_data(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        return response.json()

def get_close_price_at_specific_time(symbol, target_datetime):
    """
    Converts the target datetime to UTC and fetches the close price for the specified symbol at that time.
    """
    # Convert the target time to UTC timestamp
    target_time_utc = target_datetime.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later

    data = get_data(symbol, start_time_ms, end_time_ms)
    if data and len(data) > 0:
        close_price = float(data[0][4])  # Close price is the fifth element in the list
        return close_price
    else:
        raise ValueError("No data returned from API.")

def main():
    """
    Main function to determine if the price of BTC/USDT went up or down at a specific time.
    """
    symbol = "BTCUSDT"
    target_datetime = datetime(2025, 6, 9, 2, 0, tzinfo=pytz.timezone("US/Eastern"))

    try:
        price_at_start = get_close_price_at_specific_time(symbol, target_datetime)
        price_one_hour_later = get_close_price_at_specific_time(symbol, target_datetime + timedelta(hours=1))

        if price_one_hour_later >= price_at_start:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logger.error(f"Error fetching price data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()