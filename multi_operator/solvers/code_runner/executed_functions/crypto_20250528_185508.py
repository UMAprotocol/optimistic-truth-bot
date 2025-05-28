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
    primary_url = "https://api.binance.com/api/v3"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    
    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}/klines?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}/klines?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price

def main():
    # Example date and time for the query
    date_str = "2025-05-28"
    hour = 11  # 11 AM ET
    minute = 0
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"

    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    time_str = f"{hour:02d}:{minute:02d}:00"
    target_time_local = tz.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)

    # Get the close price at the specified time
    close_price_start = get_data(symbol, start_time_ms, start_time_ms + 60000)  # 1 minute interval

    # Get the close price at the end of the hour
    end_time_ms = start_time_ms + 3600000  # Plus 1 hour
    close_price_end = get_data(symbol, end_time_ms, end_time_ms + 60000)  # 1 minute interval

    # Determine the resolution based on the price change
    if close_price_end >= close_price_start:
        print("recommendation: p2")  # Up
    else:
        print("recommendation: p1")  # Down

if __name__ == "__main__":
    main()