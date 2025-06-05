import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# API URLs
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_data_from_api(symbol, interval, start_time, end_time):
    """
    Fetches data from the Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy API first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        logger.error(f"Proxy API failed, error: {e}")
        # Fallback to the primary API if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price
        except Exception as e:
            logger.error(f"Primary API failed, error: {e}")
            raise ConnectionError("Both primary and proxy APIs failed.")

def convert_to_utc_timestamp(date_str, time_str, timezone_str):
    """
    Converts local time to UTC timestamp.
    """
    local_tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_dt = local_tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    try:
        # Define the symbol and interval
        symbol = "BTC.D"
        interval = "1m"
        
        # Define the start and end times
        start_time_1 = convert_to_utc_timestamp("2025-05-01", "00:00", "US/Eastern")
        end_time_1 = start_time_1 + 60000  # 1 minute later in milliseconds
        
        start_time_2 = convert_to_utc_timestamp("2025-05-31", "23:59", "US/Eastern")
        end_time_2 = start_time_2 + 60000  # 1 minute later in milliseconds
        
        # Fetch close prices
        close_price_start = fetch_data_from_api(symbol, interval, start_time_1, end_time_1)
        close_price_end = fetch_data_from_api(symbol, interval, start_time_2, end_time_2)
        
        # Determine the resolution
        if close_price_start < close_price_end:
            recommendation = "p2"  # Up
        elif close_price_start > close_price_end:
            recommendation = "p1"  # Down
        else:
            recommendation = "p3"  # 50-50
        
        print(f"recommendation: {recommendation}")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()