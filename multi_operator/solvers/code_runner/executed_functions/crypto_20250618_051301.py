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

def get_binance_price(symbol, start_time):
    """
    Fetches the open and close price for a specific 1-hour candle from Binance.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"
    
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour in milliseconds
    }
    
    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return open_price, close_price
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                open_price = float(data[0][1])
                close_price = float(data[0][4])
                return open_price, close_price
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}")
            raise

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the open and close prices.
    """
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to execute the market resolution logic.
    """
    # Define the specific time for the market resolution
    target_date_str = "2025-06-18"
    target_hour = 0  # 12 AM ET
    target_minute = 0
    timezone_str = "US/Eastern"
    
    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    target_time_local = tz.localize(datetime.strptime(f"{target_date_str} {target_hour:02d}:{target_minute:02d}:00", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    
    # Fetch the open and close prices
    try:
        open_price, close_price = get_binance_price("BTCUSDT", start_time_ms)
        logger.info(f"Open price: {open_price}, Close price: {close_price}")
        
        # Resolve the market
        resolution = resolve_market(open_price, close_price)
        print(f"recommendation: {resolution}")
    except Exception as e:
        logger.error(f"Failed to resolve market: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()