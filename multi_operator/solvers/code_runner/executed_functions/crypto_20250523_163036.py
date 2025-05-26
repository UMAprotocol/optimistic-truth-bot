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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_data(symbol, start_time, end_time, proxy_url, primary_url):
    """
    Fetches data from Binance API using a proxy and falls back to the primary endpoint if necessary.
    """
    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}/klines?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        return response.json()

def convert_to_utc_timestamp(date_str, hour, minute, timezone_str):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
    local_dt = tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    symbol = "SOLUSDT"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3"
    
    # Convert local time to UTC timestamps
    start_time_22 = convert_to_utc_timestamp("2025-05-22", 12, 0, "US/Eastern")
    end_time_22 = start_time_22 + 60000  # 1 minute later in milliseconds
    
    start_time_23 = convert_to_utc_timestamp("2025-05-23", 12, 0, "US/Eastern")
    end_time_23 = start_time_23 + 60000  # 1 minute later in milliseconds
    
    # Fetch data
    data_22 = get_data(symbol, start_time_22, end_time_22, proxy_url, primary_url)
    data_23 = get_data(symbol, start_time_23, end_time_23, proxy_url, primary_url)
    
    # Extract close prices
    close_price_22 = float(data_22[0][4])
    close_price_23 = float(data_23[0][4])
    
    # Determine resolution
    if close_price_23 > close_price_22:
        resolution = "p2"  # Up
    elif close_price_23 < close_price_22:
        resolution = "p1"  # Down
    else:
        resolution = "p3"  # 50-50
    
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()