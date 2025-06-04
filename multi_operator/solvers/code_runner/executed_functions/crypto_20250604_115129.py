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

def fetch_binance_price(symbol, start_time):
    """
    Fetches the closing price of a cryptocurrency from Binance for a specific 1-hour candle.

    Args:
        symbol (str): The symbol to fetch, e.g., 'BTCUSDT'
        start_time (datetime): The start time of the 1-hour candle

    Returns:
        float: The closing price of the candle
    """
    # Convert datetime to milliseconds since epoch
    start_time_ms = int(start_time.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later

    # URLs setup
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    # Parameters for the API call
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": start_time_ms,
        "endTime": end_time_ms
    }

    try:
        # Try fetching via proxy first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            close_price = float(data[0][4])
            return close_price
    except Exception as e:
        logger.error(f"Proxy failed, error: {e}, trying primary endpoint.")
        try:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                close_price = float(data[0][4])
                return close_price
        except Exception as e:
            logger.error(f"Primary endpoint also failed, error: {e}")
            raise

def main():
    # Specific date and time for the query
    target_date_str = "2025-05-30"
    target_time_str = "16:00:00"
    timezone_str = "US/Eastern"

    # Convert the target time to UTC
    tz = pytz.timezone(timezone_str)
    target_datetime = datetime.strptime(f"{target_date_str} {target_time_str}", "%Y-%m-%d %H:%M:%S")
    target_datetime = tz.localize(target_datetime).astimezone(pytz.utc)

    # Symbol for the cryptocurrency
    symbol = "BTCUSDT"

    try:
        # Fetch the closing price for the specified time
        closing_price = fetch_binance_price(symbol, target_datetime)
        logger.info(f"Closing price for {symbol} at {target_datetime} UTC is {closing_price}")

        # Output the recommendation based on the closing price
        if closing_price >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    main()