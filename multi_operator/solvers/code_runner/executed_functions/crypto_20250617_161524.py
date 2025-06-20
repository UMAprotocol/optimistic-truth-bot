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
        symbol (str): The symbol of the cryptocurrency (e.g., 'BTCUSDT').
        target_time (datetime): The target datetime in UTC.

    Returns:
        float: The closing price of the cryptocurrency.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_time.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later

    # URLs for Binance API
    primary_url = "https://api.binance.com/api/v3/klines"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

    # Parameters for the API call
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try using the proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        logger.error(f"Proxy failed, error: {e}, trying primary endpoint.")
        # Fallback to the primary endpoint
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            close_price = float(data[0][4])
            return close_price
        except Exception as e:
            logger.error(f"Both proxy and primary endpoints failed, error: {e}")
            raise

def main():
    """
    Main function to check if Bitcoin's price was above $110,000 on June 17, 2025 at 12:00 ET.
    """
    try:
        # Define the target date and time
        target_date_str = "2025-06-17"
        target_time = datetime.strptime(target_date_str, "%Y-%m-%d")
        target_time = pytz.timezone("US/Eastern").localize(datetime(target_time.year, target_time.month, target_time.day, 12, 0, 0))
        target_time_utc = target_time.astimezone(pytz.utc)

        # Get the price of Bitcoin at the specified time
        btc_price = get_binance_price("BTCUSDT", target_time_utc)

        # Check if the price was above $110,000
        if btc_price > 110000:
            print("recommendation: p2")  # Yes
        else:
            print("recommendation: p1")  # No
    except Exception as e:
        logger.error(f"Failed to retrieve or process data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()