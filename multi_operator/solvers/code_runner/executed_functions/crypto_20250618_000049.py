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
    Resolves the market based on the open and close prices of the specified symbol at the target time.
    """
    # Convert target time to UTC timestamp in milliseconds
    target_datetime = datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")
    target_timestamp = int(target_datetime.replace(tzinfo=timezone.utc).timestamp() * 1000)

    # Fetch the data for the specific hour
    candle_data = get_data(symbol, target_timestamp, target_timestamp + 3600000)  # 1 hour in milliseconds

    if candle_data:
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])
        logger.info(f"Open price: {open_price}, Close price: {close_price}")

        # Determine resolution based on open and close prices
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data available

def main():
    """
    Main function to handle the resolution of the market.
    """
    # Example: Solana price on June 17, 2025, 7PM ET
    symbol = "SOLUSDT"
    target_time = "2025-06-17 19:00:00"

    # Convert ET to UTC
    et_timezone = pytz.timezone("US/Eastern")
    naive_datetime = datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")
    local_dt = et_timezone.localize(naive_datetime)
    utc_dt = local_dt.astimezone(pytz.utc)

    # Format UTC datetime to string
    utc_time_str = utc_dt.strftime("%Y-%m-%d %H:%M:%S")

    # Resolve the market
    resolution = resolve_market(symbol, utc_time_str)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()