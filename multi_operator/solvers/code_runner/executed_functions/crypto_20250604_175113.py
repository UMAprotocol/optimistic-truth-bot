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

def get_data(symbol, start_time, end_time):
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"
    
    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    raise Exception("Failed to retrieve data from both endpoints")

def convert_to_utc_timestamp(date_str, hour, minute, timezone_str):
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    return int(utc_datetime.timestamp() * 1000)  # Convert to milliseconds

def main():
    symbol = "XRPUSDT"
    timezone_str = "US/Eastern"
    start_date = "2025-05-31"
    end_date = "2025-06-01"
    hour = 12
    minute = 0

    start_time = convert_to_utc_timestamp(start_date, hour, minute, timezone_str)
    end_time = convert_to_utc_timestamp(end_date, hour, minute, timezone_str)

    try:
        close_price_start = get_data(symbol, start_time, start_time + 60000)  # 1 minute in milliseconds
        close_price_end = get_data(symbol, end_time, end_time + 60000)

        if close_price_start < close_price_end:
            recommendation = "p2"  # Up
        elif close_price_start > close_price_end:
            recommendation = "p1"  # Down
        else:
            recommendation = "p3"  # 50-50
    except Exception as e:
        logging.error(f"Error retrieving data: {e}")
        recommendation = "p4"  # Unable to resolve

    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()