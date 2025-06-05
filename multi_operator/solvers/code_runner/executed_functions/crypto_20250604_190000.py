import requests
import logging
from datetime import datetime, timezone
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

def get_binance_price(symbol, target_time):
    """
    Fetches the closing price of a cryptocurrency at a specific time from Binance.

    Args:
        symbol (str): The symbol of the cryptocurrency pair (e.g., 'BTCUSDT').
        target_time (datetime): The target datetime in UTC.

    Returns:
        float: The closing price of the cryptocurrency.
    """
    # Convert datetime to milliseconds since epoch
    target_time_ms = int(target_time.timestamp() * 1000)

    # URLs for Binance API
    primary_url = "https://api.binance.com/api/v3/klines"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

    # Parameters for the API request
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": target_time_ms,
        "endTime": target_time_ms + 60000  # 1 minute range
    }

    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        logger.error(f"Proxy failed, error: {e}. Trying primary endpoint.")
        try:
            # Fallback to the primary endpoint if proxy fails
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            close_price = float(data[0][4])
            return close_price
        except Exception as e:
            logger.error(f"Both proxy and primary endpoint failed, error: {e}")
            raise

def main():
    # Specific date and time for the query
    target_time_utc = datetime(2025, 6, 4, 14, 0, tzinfo=timezone.utc)
    symbol = "BTCUSDT"

    try:
        close_price = get_binance_price(symbol, target_time_utc)
        logger.info(f"Close price for {symbol} at {target_time_utc} UTC is {close_price}")

        # Check if the price is above or equal to 230,000 USDT
        if close_price >= 230000:
            print("recommendation: p2")  # Yes
        else:
            print("recommendation: p1")  # No
    except Exception as e:
        logger.error(f"Failed to retrieve or process data: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()