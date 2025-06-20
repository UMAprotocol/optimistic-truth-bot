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

def get_data(symbol, start_time, end_time):
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3"
    
    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}/klines?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        return response.json()

def convert_to_utc_timestamp(date_str, hour, minute, timezone_str):
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    return int(utc_datetime.timestamp() * 1000)

def main():
    symbol = "ETHUSDT"
    timezone_str = "US/Eastern"
    date1_str = "2025-06-14"
    date2_str = "2025-06-15"
    hour = 12
    minute = 0

    start_time1 = convert_to_utc_timestamp(date1_str, hour, minute, timezone_str)
    end_time1 = start_time1 + 60000  # 1 minute in milliseconds

    start_time2 = convert_to_utc_timestamp(date2_str, hour, minute, timezone_str)
    end_time2 = start_time2 + 60000  # 1 minute in milliseconds

    data1 = get_data(symbol, start_time1, end_time1)
    data2 = get_data(symbol, start_time2, end_time2)

    close_price1 = float(data1[0][4])
    close_price2 = float(data2[0][4])

    if close_price1 < close_price2:
        recommendation = "p2"  # Up
    elif close_price1 > close_price2:
        recommendation = "p1"  # Down
    else:
        recommendation = "p3"  # 50-50

    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()