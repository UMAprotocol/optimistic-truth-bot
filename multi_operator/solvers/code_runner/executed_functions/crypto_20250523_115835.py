import requests
import logging
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

# API endpoints and keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

def get_data(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # First try the proxy endpoint
        response = requests.get(f"{PROXY_URL}", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_URL}/klines", params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def check_hyperliquid_price():
    """
    Checks if the price of HYPE/USDC reached $35 or higher between the specified dates.
    """
    symbol = "HYPEUSDC"
    start_date = datetime(2025, 5, 7, 16, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone("US/Eastern"))
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)

    try:
        data = get_data(symbol, start_time, end_time)
        for candle in data:
            high_price = float(candle[2])  # High price is the third element in the list
            if high_price >= 35.0:
                logger.info(f"High price of {high_price} reached or exceeded $35.0")
                return "p2"  # Yes, price reached $35 or higher
        logger.info("Price did not reach $35.0")
        return "p1"  # No, price did not reach $35
    except Exception as e:
        logger.error(f"Error fetching or processing data: {e}")
        return "p3"  # Unknown/50-50 if there's an error

def main():
    """
    Main function to run the price check.
    """
    result = check_hyperliquid_price()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()