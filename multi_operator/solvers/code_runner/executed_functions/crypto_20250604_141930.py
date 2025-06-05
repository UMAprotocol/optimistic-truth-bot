import requests
import logging
from datetime import datetime, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

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
        response = requests.get(f"{PROXY_URL}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price
        except Exception as ex:
            logger.error(f"Primary endpoint also failed: {str(ex)}")
            raise

def convert_to_utc_timestamp(date_str, timezone_str="US/Eastern"):
    """
    Converts a date string with timezone to a UTC timestamp.
    """
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    return int(utc_datetime.timestamp() * 1000)

def main():
    """
    Main function to determine if Bitcoin Dominance went up or down in May 2025.
    """
    try:
        start_time = convert_to_utc_timestamp("2025-05-01 00:00", "US/Eastern")
        end_time = convert_to_utc_timestamp("2025-05-31 23:59", "US/Eastern")
        
        start_price = get_data("BTC.D", start_time, start_time + 60000)  # 1 minute in milliseconds
        end_price = get_data("BTC.D", end_time, end_time + 60000)
        
        if start_price < end_price:
            print("recommendation: p2")  # Up
        elif start_price > end_price:
            print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # 50-50
    except Exception as e:
        logger.error(f"Failed to process data: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()