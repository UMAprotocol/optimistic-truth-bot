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
        try:
            response = requests.get(f"{primary_url}?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {str(e)}")
            raise

def resolve_market(symbol, target_date):
    """
    Resolves the market based on the price change of the cryptocurrency from the start to the end of the specified hour.
    """
    tz = pytz.timezone("US/Eastern")
    target_datetime = tz.localize(datetime.strptime(target_date, "%Y-%m-%d %H:%M:%S"))
    start_time_ms = int(target_datetime.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour in milliseconds

    try:
        candle_data = get_data(symbol, start_time_ms, end_time_ms)
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])

        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    except Exception as e:
        logger.error(f"Error resolving market: {e}")
        return "recommendation: p3"  # Unknown/50-50 if error occurs

def main():
    """
    Main function to handle the resolution of the Bitcoin Up or Down market.
    """
    symbol = "BTCUSDT"
    target_date = "2025-05-29 01:00:00"
    result = resolve_market(symbol, target_date)
    print(result)

if __name__ == "__main__":
    main()