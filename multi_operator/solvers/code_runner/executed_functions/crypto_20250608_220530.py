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

def resolve_market(symbol, target_date):
    """
    Resolves the market based on the price change of the specified symbol on the target date.
    """
    tz = pytz.timezone("US/Eastern")
    target_datetime = datetime.strptime(target_date, "%Y-%m-%d %H:%M")
    target_datetime = tz.localize(target_datetime)
    start_time_utc = int(target_datetime.timestamp() * 1000)
    end_time_utc = start_time_utc + 3600000  # 1 hour later

    data = get_data(symbol, start_time_utc, end_time_utc)
    if data:
        open_price = float(data[1])
        close_price = float(data[4])
        change_percentage = ((close_price - open_price) / open_price) * 100

        if change_percentage >= 0:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    """
    Main function to handle the resolution of the market.
    """
    try:
        result = resolve_market("BTCUSDT", "2025-06-08 17:00")
        print(result)
    except Exception as e:
        logger.error(f"Error resolving market: {e}")
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()