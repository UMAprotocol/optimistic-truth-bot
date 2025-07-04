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
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]

def resolve_market():
    """
    Resolves the market based on the change in BTC/USDT price for the specified candle.
    """
    symbol = "BTCUSDT"
    interval = "1h"
    target_date = datetime(2025, 5, 28, 13, 0, 0, tzinfo=pytz.timezone("US/Eastern"))  # 1 PM ET
    start_time = int(target_date.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    candle_data = get_data(symbol, interval, start_time, end_time)
    if candle_data:
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])
        change_percentage = ((close_price - open_price) / open_price) * 100

        if change_percentage >= 0:
            logger.info(f"Market resolves to Up. Change: {change_percentage}%")
            return "recommendation: p2"  # Up
        else:
            logger.info(f"Market resolves to Down. Change: {change_percentage}%")
            return "recommendation: p1"  # Down
    else:
        logger.error("Failed to retrieve data for the specified candle.")
        return "recommendation: p3"  # Unknown/50-50

def main():
    result = resolve_market()
    print(result)

if __name__ == "__main__":
    main()