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
        symbol (str): The symbol of the cryptocurrency, e.g., 'BTCUSDT'.
        target_time (datetime): The target datetime in UTC.

    Returns:
        float: The closing price of the cryptocurrency.
    """
    # Convert datetime to milliseconds since epoch
    target_time_ms = int(target_time.timestamp() * 1000)

    # URLs for Binance API
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    # Parameters for API request
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
    """
    Main function to check if Bitcoin's price was above $103,000 on June 13, 2025 at 12:00 ET.
    """
    try:
        # Define the target time in Eastern Time
        et_timezone = pytz.timezone("US/Eastern")
        target_time_et = et_timezone.localize(datetime(2025, 6, 13, 12, 0, 0))
        # Convert to UTC
        target_time_utc = target_time_et.astimezone(pytz.utc)

        # Get the closing price of BTCUSDT at the specified time
        close_price = get_binance_price("BTCUSDT", target_time_utc)

        # Check if the price is above $103,000
        if close_price > 103000:
            print("recommendation: p2")  # Yes
        else:
            print("recommendation: p1")  # No
    except Exception as e:
        logger.error(f"Failed to retrieve or process data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()