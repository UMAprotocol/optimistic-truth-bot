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

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of the specified symbol at the given datetime.
    """
    # Convert datetime to UTC timestamp in milliseconds
    target_timestamp = int(target_datetime.timestamp() * 1000)

    # Fetch data for the specific hour
    data = get_data(symbol, target_timestamp, target_timestamp + 3600000)  # 1 hour in milliseconds

    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = close_price - open_price

        if price_change >= 0:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data available

def main():
    """
    Main function to handle the resolution of the Ethereum market for June 14, 9 AM ET.
    """
    # Define the target date and time
    target_date_str = "2025-06-14"
    target_time_str = "09:00:00"
    timezone_str = "US/Eastern"

    # Convert the target time to UTC
    tz = pytz.timezone(timezone_str)
    target_datetime_local = tz.localize(datetime.strptime(f"{target_date_str} {target_time_str}", "%Y-%m-%d %H:%M:%S"))
    target_datetime_utc = target_datetime_local.astimezone(timezone.utc)

    # Symbol for the market
    symbol = "ETHUSDT"

    # Resolve the market
    resolution = resolve_market(symbol, target_datetime_utc)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()