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

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}. Trying primary endpoint.")

        # Fallback to primary endpoint
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}.")
            raise

def get_candle_data(date_str, hour, timezone_str, symbol):
    """
    Retrieves the closing price of a specific 1-hour candle on Binance.
    """
    tz = pytz.timezone(timezone_str)
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    dt = tz.localize(datetime(dt.year, dt.month, dt.day, hour, 0, 0))
    dt_utc = dt.astimezone(pytz.utc)

    start_time = int(dt_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour in milliseconds

    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        close_price = float(data[0][4])
        open_price = float(data[0][1])
        return close_price, open_price
    else:
        logger.error("No data available for the specified time.")
        return None, None

def main():
    """
    Main function to determine if the Bitcoin price went up or down for the specified candle.
    """
    date_str = "2025-05-28"
    hour = 7  # 7 AM ET
    timezone_str = "US/Eastern"
    symbol = "BTCUSDT"

    try:
        close_price, open_price = get_candle_data(date_str, hour, timezone_str, symbol)
        if close_price is not None and open_price is not None:
            if close_price >= open_price:
                print("recommendation: p2")  # Up
            else:
                print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # Unknown/50-50
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()