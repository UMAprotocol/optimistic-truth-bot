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
        logger.error(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])

def fetch_ethereum_price(date_str, hour=12, minute=0, timezone_str="US/Eastern"):
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    start_time = int(utc_datetime.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later in milliseconds

    price = get_data("ETHUSDT", start_time, end_time)
    return price

def main():
    target_date = "2025-06-17"
    target_price = 2800
    try:
        price = fetch_ethereum_price(target_date)
        if price is not None:
            if price > target_price:
                recommendation = "p2"  # Yes, price is above $2800
            else:
                recommendation = "p1"  # No, price is not above $2800
        else:
            recommendation = "p3"  # Unknown/50-50 if no data is available
    except Exception as e:
        logger.error(f"Error fetching price: {e}")
        recommendation = "p3"  # Unknown/50-50 in case of error

    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()