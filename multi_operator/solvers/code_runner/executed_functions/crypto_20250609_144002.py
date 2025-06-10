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
    primary_url = "https://api.binance.com/api/v3/klines"
    
    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{primary_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {str(e)}")
            raise

def convert_to_utc_timestamp(date_str, hour, minute, timezone_str):
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    return int(utc_datetime.timestamp() * 1000)

def main():
    symbol = "SOLUSDT"
    date_str = "2025-05-30"
    hour = 12
    minute = 0
    timezone_str = "US/Eastern"
    threshold = 200.01

    start_time = convert_to_utc_timestamp(date_str, hour, minute, timezone_str)
    end_time = start_time + 60000  # 1 minute later in milliseconds

    try:
        close_price = get_data(symbol, start_time, end_time)
        if close_price >= threshold:
            recommendation = "p2"  # Yes, price is above $200
        else:
            recommendation = "p1"  # No, price is not above $200
    except Exception as e:
        logger.error(f"Failed to retrieve or process data: {e}")
        recommendation = "p3"  # Unknown/50-50 if there's an error

    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()