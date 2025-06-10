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

def get_binance_data(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try proxy endpoint first
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Close price
    except Exception as e:
        logger.error(f"Proxy failed, error: {e}, trying primary API")
        try:
            # Fallback to primary endpoint
            response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data[0][4])  # Close price
        except Exception as e:
            logger.error(f"Primary API failed, error: {e}")
            raise

def convert_to_utc_timestamp(date_str, hour, minute, tz_str="US/Eastern"):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(tz_str)
    local_dt = tz.localize(datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S"))
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    """
    Main function to determine if the price of SOLUSDT went up or down between two specific times.
    """
    try:
        # Define the dates and times
        date1 = "2025-06-08"
        date2 = "2025-06-09"
        hour = 12
        minute = 0
        symbol = "SOLUSDT"
        
        # Convert times to UTC timestamps
        start_time1 = convert_to_utc_timestamp(date1, hour, minute)
        end_time1 = start_time1 + 60000  # 1 minute later in milliseconds
        start_time2 = convert_to_utc_timestamp(date2, hour, minute)
        end_time2 = start_time2 + 60000  # 1 minute later in milliseconds
        
        # Get close prices
        close_price1 = get_binance_data(symbol, start_time1, end_time1)
        close_price2 = get_binance_data(symbol, start_time2, end_time2)
        
        # Determine the resolution
        if close_price2 > close_price1:
            print("recommendation: p2")  # Up
        elif close_price2 < close_price1:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        logger.error(f"Failed to process data: {e}")
        print("recommendation: p4")  # Unknown or error

if __name__ == "__main__":
    main()