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

# Binance API URLs
PRIMARY_BINANCE_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_BINANCE_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logger.error(f"Proxy failed with error: {e}. Trying primary endpoint.")
        # If proxy fails, fallback to the primary endpoint
        try:
            response = requests.get(PRIMARY_BINANCE_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Primary endpoint also failed with error: {e}.")
            raise

def get_close_price(symbol, date_str, timezone_str="US/Eastern"):
    """
    Get the close price for a specific minute candle on Binance.
    """
    tz = pytz.timezone(timezone_str)
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    dt = tz.localize(dt).astimezone(pytz.utc)
    start_time = int(dt.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later in milliseconds

    data = fetch_binance_data(symbol, "1m", start_time, end_time)
    if data and len(data) > 0:
        close_price = float(data[0][4])  # Close price is the 5th element
        return close_price
    else:
        logger.error("No data returned from Binance.")
        return None

def main():
    """
    Main function to determine if the XRP price went up or down between two specific times.
    """
    symbol = "XRPUSDT"
    date1 = "2025-05-25 12:00"
    date2 = "2025-05-26 12:00"

    try:
        price1 = get_close_price(symbol, date1)
        price2 = get_close_price(symbol, date2)

        if price1 is None or price2 is None:
            print("recommendation: p4")
        elif price2 > price1:
            print("recommendation: p2")
        elif price2 < price1:
            print("recommendation: p1")
        else:
            print("recommendation: p3")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p4")

if __name__ == "__main__":
    main()