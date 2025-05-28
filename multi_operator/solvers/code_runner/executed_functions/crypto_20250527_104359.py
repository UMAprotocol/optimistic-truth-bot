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
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def get_data(symbol, start_time, end_time):
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3"
    
    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{primary_url}/klines?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {str(e)}")
            raise

def main():
    symbol = "BTCUSDT"
    target_time = datetime(2025, 5, 27, 23, 0, 0, tzinfo=pytz.timezone("Asia/Shanghai"))
    target_time_utc = target_time.astimezone(pytz.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 60000  # 1 minute later

    try:
        price = get_data(symbol, start_time_ms, end_time_ms)
        logger.info(f"Price of {symbol} at {target_time.strftime('%Y-%m-%d %H:%M:%S %Z')} is {price}")
        if price > 150000:
            print("recommendation: p1")
        else:
            print("recommendation: p2")
    except Exception as e:
        logger.error(f"Failed to retrieve data: {e}")
        print("recommendation: p4")

if __name__ == "__main__":
    main()