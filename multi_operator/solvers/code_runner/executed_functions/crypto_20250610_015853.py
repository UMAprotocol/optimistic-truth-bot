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

def get_binance_price(symbol, target_time):
    """
    Fetches the closing price of a cryptocurrency at a specific time from Binance.

    Args:
        symbol (str): The symbol of the cryptocurrency pair (e.g., 'BTCUSDT').
        target_time (datetime): The target datetime object in UTC.

    Returns:
        float: The closing price of the cryptocurrency.
    """
    # Convert datetime to milliseconds since epoch
    target_time_ms = int(target_time.timestamp() * 1000)

    # URLs for Binance API
    primary_url = "https://api.binance.com/api/v3/klines"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

    # Parameters for the API call
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": target_time_ms,
        "endTime": target_time_ms + 60000  # 1 minute range
    }

    try:
        # Try using the proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        logger.error(f"Proxy failed, error: {e}. Trying primary endpoint.")
        # Fallback to the primary endpoint if proxy fails
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            close_price = float(data[0][4])
            return close_price
        except Exception as e:
            logger.error(f"Both proxy and primary endpoint failed, error: {e}")
            raise

def main():
    # Define the specific date and time for the query
    date_str = "2025-05-16"
    hour = 12  # Noon
    minute = 0
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"

    # Convert local time to UTC
    tz = pytz.timezone(timezone_str)
    local_time = tz.localize(datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S"))
    utc_time = local_time.astimezone(pytz.utc)

    try:
        # Get the closing price from Binance
        close_price = get_binance_price(symbol, utc_time)
        logger.info(f"Close price for {symbol} at {utc_time} UTC is {close_price}")

        # Determine the resolution based on the close price
        if close_price <= 95999.99:
            print("recommendation: p2")  # Yes, it closed below $96K
        else:
            print("recommendation: p1")  # No, it did not close below $96K
    except Exception as e:
        logger.error(f"Failed to retrieve or process data: {e}")
        print("recommendation: p4")  # Unable to resolve due to error

if __name__ == "__main__":
    main()