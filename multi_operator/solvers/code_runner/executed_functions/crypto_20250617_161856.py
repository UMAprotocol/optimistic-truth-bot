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

def get_binance_price(symbol, interval, start_time):
    """
    Fetches the price data from Binance API for a given symbol and interval at a specific start time.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"
    
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }
    
    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        logger.error(f"Proxy failed with error: {e}, trying primary endpoint.")
        # Fallback to primary endpoint
        try:
            response = requests.get(primary_url, params=params)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            logger.error(f"Primary endpoint also failed with error: {e}")
            raise

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the symbol at the specified target time.
    """
    try:
        # Convert target time to UTC milliseconds
        target_time_utc = int(target_time.replace(tzinfo=timezone.utc).timestamp() * 1000)
        candle_data = get_binance_price(symbol, "1h", target_time_utc)
        
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])
        
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    except Exception as e:
        logger.error(f"Error resolving market: {e}")
        return "p3"  # Unknown/50-50 if error occurs

def main():
    """
    Main function to execute the market resolution.
    """
    # Example: June 17, 2025, 11 AM ET
    target_time = datetime(2025, 6, 17, 11, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "BTCUSDT"
    result = resolve_market(symbol, target_time)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()