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

def get_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the specified symbol at the given target time.
    """
    # Convert target time to UTC timestamp in milliseconds
    target_time_utc = target_time.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later

    # Fetch data for the 1 hour interval
    data = get_data(symbol, "1h", start_time_ms, end_time_ms)
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        change_percentage = ((close_price - open_price) / open_price) * 100

        # Determine resolution based on the change percentage
        if change_percentage >= 0:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data

def main():
    """
    Main function to handle the resolution of the Ethereum Up or Down market.
    """
    # Define the target time for the market resolution
    target_time_str = "2025-06-15 15:00:00"
    timezone_str = "US/Eastern"
    symbol = "ETHUSDT"

    # Parse the target time
    tz = pytz.timezone(timezone_str)
    target_time = tz.localize(datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S"))

    # Resolve the market
    resolution = resolve_market(symbol, target_time)

    # Output the recommendation
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()