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
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0][4]  # Close price of the candle
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{primary_url}/klines?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0][4]  # Close price of the candle
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {str(e)}")
            raise

def resolve_market(date_str, hour=12, minute=0, timezone_str="US/Eastern", symbol="BTCUSDT"):
    tz = pytz.timezone(timezone_str)
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    dt = tz.localize(datetime(dt.year, dt.month, dt.day, hour, minute, 0))
    dt_utc = dt.astimezone(pytz.utc)
    start_time = int(dt_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    close_price_start = float(get_data(symbol, start_time, start_time + 60000))  # Start of the candle
    close_price_end = float(get_data(symbol, end_time - 60000, end_time))  # End of the candle

    if close_price_end >= close_price_start:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    try:
        resolution = resolve_market("2025-05-30")
        print(f"recommendation: {resolution}")
    except Exception as e:
        logger.error(f"Failed to resolve market due to: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()