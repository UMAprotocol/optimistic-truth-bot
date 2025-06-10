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

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logger.error(f"Proxy failed with error: {e}. Trying primary endpoint.")
        # Fallback to the primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Primary endpoint failed with error: {e}.")
            raise

def get_close_price(data):
    """
    Extracts the close price from Binance API data.
    """
    if data and len(data) > 0:
        return float(data[0][4])
    else:
        raise ValueError("No data available to extract close price.")

def convert_to_utc_timestamp(date_str, hour, minute, tz_str):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(tz_str)
    local_dt = tz.localize(datetime.strptime(date_str, "%Y-%m-%d"))
    local_dt = local_dt.replace(hour=hour, minute=minute)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    try:
        # Define the dates, times, and symbol
        symbol = "XRPUSDT"
        date1_str = "2025-05-29"
        date2_str = "2025-05-30"
        hour = 12
        minute = 0
        tz_str = "US/Eastern"

        # Convert dates and times to UTC timestamps
        start_time1 = convert_to_utc_timestamp(date1_str, hour, minute, tz_str)
        end_time1 = start_time1 + 60000  # 1 minute later in milliseconds
        start_time2 = convert_to_utc_timestamp(date2_str, hour, minute, tz_str)
        end_time2 = start_time2 + 60000

        # Fetch data from Binance
        data1 = fetch_binance_data(symbol, start_time1, end_time1)
        data2 = fetch_binance_data(symbol, start_time2, end_time2)

        # Get close prices
        close_price1 = get_close_price(data1)
        close_price2 = get_close_price(data2)

        # Determine the resolution based on close prices
        if close_price1 < close_price2:
            print("recommendation: p2")  # Up
        elif close_price1 > close_price2:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()