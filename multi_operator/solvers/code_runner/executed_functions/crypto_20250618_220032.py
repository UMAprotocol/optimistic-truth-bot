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
            return data[0]  # Return the first (and only) entry
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]  # Return the first (and only) entry

def resolve_market():
    """
    Resolves the market based on the BTC/USDT price data from Binance.
    """
    # Define the specific date and time for the event
    event_datetime = datetime(2025, 6, 18, 17, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    event_timestamp = int(event_datetime.timestamp() * 1000)  # Convert to milliseconds

    # Fetch the data for the specific hour candle
    candle_data = get_data("BTCUSDT", event_timestamp, event_timestamp + 3600000)  # 1 hour in milliseconds

    if candle_data:
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])

        # Determine the resolution based on the open and close prices
        if close_price >= open_price:
            logger.info("Market resolves to 'Up'")
            return "recommendation: p2"  # Up
        else:
            logger.info("Market resolves to 'Down'")
            return "recommendation: p1"  # Down
    else:
        logger.error("No data available to resolve the market.")
        return "recommendation: p3"  # Unknown/50-50

def main():
    """
    Main function to execute the market resolution.
    """
    result = resolve_market()
    print(result)

if __name__ == "__main__":
    main()