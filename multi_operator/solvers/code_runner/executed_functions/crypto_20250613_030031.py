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
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the symbol at the specified target time.
    """
    # Convert target time to UTC timestamp in milliseconds
    target_datetime = datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")
    target_timestamp = int(target_datetime.replace(tzinfo=timezone.utc).timestamp() * 1000)

    # Get data for the specified hour
    candle_data = get_data(symbol, target_timestamp, target_timestamp + 3600000)  # 1 hour in milliseconds

    if candle_data:
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])
        price_change_percentage = ((close_price - open_price) / open_price) * 100

        # Determine resolution based on price change
        if price_change_percentage >= 0:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50 if no data

def main():
    """
    Main function to handle the resolution of the market.
    """
    # Example date and time for the market resolution
    target_time = "2025-06-12 22:00:00"  # June 12, 2025, 10 PM ET
    symbol = "BTCUSDT"

    try:
        resolution = resolve_market(symbol, target_time)
        print(resolution)
    except Exception as e:
        logger.error(f"Error resolving market: {e}")
        print("recommendation: p3")  # Unknown/50-50 in case of error

if __name__ == "__main__":
    main()