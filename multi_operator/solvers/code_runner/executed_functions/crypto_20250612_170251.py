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
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def get_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy if the primary endpoint fails.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    try:
        # Try proxy endpoint first
        response = requests.get(
            f"{proxy_url}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logger.error(f"Proxy failed, error: {e}. Trying primary endpoint.")

        # Fallback to primary endpoint
        try:
            response = requests.get(
                f"{primary_url}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Primary endpoint also failed, error: {e}.")
            raise

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the symbol at the specified target time.
    """
    # Convert target time to UTC milliseconds
    target_datetime = datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")
    target_timestamp = int(target_datetime.replace(tzinfo=timezone.utc).timestamp() * 1000)

    # Get data for the specified hour
    data = get_binance_data(symbol, "1h", target_timestamp, target_timestamp + 3600000)

    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = close_price - open_price

        if price_change >= 0:
            logger.info("Market resolves to Up.")
            return "recommendation: p2"  # Up
        else:
            logger.info("Market resolves to Down.")
            return "recommendation: p1"  # Down
    else:
        logger.error("No data available to resolve the market.")
        return "recommendation: p3"  # Unknown/50-50

def main():
    """
    Main function to execute the market resolution.
    """
    try:
        # Example: Resolve for BTC/USDT on June 12, 2025, 12:00 PM ET
        target_time = "2025-06-12 12:00:00"
        symbol = "BTCUSDT"
        result = resolve_market(symbol, target_time)
        print(result)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()