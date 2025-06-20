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
    Fetches the 1-minute candle close price for a cryptocurrency pair on Binance
    at a specific time using both a proxy and a primary endpoint with fallback.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"
    
    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            close_price = float(data[0][4])
            logger.info(f"Successfully retrieved price from proxy: {close_price}")
            return close_price
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            close_price = float(data[0][4])
            logger.info(f"Successfully retrieved price from primary endpoint: {close_price}")
            return close_price

def main():
    """
    Main function to handle the cryptocurrency price query for XRP on June 13, 2025, at 12:00 ET.
    """
    symbol = "XRPUSDT"
    date_str = "2025-06-13"
    hour = 12
    minute = 0
    timezone_str = "US/Eastern"
    
    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    time_str = f"{hour:02d}:{minute:02d}:00"
    target_time_local = tz.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    
    # Fetch the close price at the specified time
    close_price = get_data(symbol, start_time_ms, start_time_ms + 60000)  # 1 minute interval
    
    # Determine the resolution based on the price
    threshold_price = 2.10
    if close_price > threshold_price:
        recommendation = "p2"  # Yes, price is above $2.10
    else:
        recommendation = "p1"  # No, price is not above $2.10
    
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()