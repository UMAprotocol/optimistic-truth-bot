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
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Binance API URLs
PRIMARY_BINANCE_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary request fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data from the proxy first
        response = requests.get(PROXY_BINANCE_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logger.error(f"Proxy failed with error: {e}. Trying primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_BINANCE_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logger.error(f"Primary API also failed with error: {e}.")
            raise

def get_close_price(symbol, date_str, timezone_str="US/Eastern"):
    """
    Retrieves the close price for a given symbol at a specified date and time.
    """
    tz = pytz.timezone(timezone_str)
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    dt_utc = tz.localize(dt).astimezone(pytz.utc)
    start_time = int(dt_utc.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later in milliseconds

    data = fetch_binance_data(symbol, "1m", start_time, end_time)
    if data and len(data) > 0:
        close_price = float(data[0][4])  # Close price is the 5th element in the list
        return close_price
    else:
        raise ValueError("No data returned from API.")

def main():
    """
    Main function to determine if Bitcoin price went up or down between two specific times.
    """
    try:
        # Define the times to check
        close_price_yesterday = get_close_price("BTCUSDT", "2025-06-15 12:00", "US/Eastern")
        close_price_today = get_close_price("BTCUSDT", "2025-06-16 12:00", "US/Eastern")

        # Determine if the price went up or down
        if close_price_today > close_price_yesterday:
            result = "p2"  # Up
        elif close_price_today < close_price_yesterday:
            result = "p1"  # Down
        else:
            result = "p3"  # 50-50

        print(f"recommendation: {result}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()