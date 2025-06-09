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
    Fetches price data from Binance API for a specific symbol and interval.
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
        return data[0][4]  # Close price of the candle
    except Exception as e:
        logger.error(f"Proxy failed, trying primary endpoint: {e}")
        # Fallback to primary endpoint
        try:
            response = requests.get(primary_url, params=params)
            response.raise_for_status()
            data = response.json()
            return data[0][4]  # Close price of the candle
        except Exception as e:
            logger.error(f"Both proxy and primary endpoints failed: {e}")
            raise

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance.
    """
    symbol = "BTCUSDT"
    interval = "1h"
    target_date = datetime(2025, 6, 5, 16, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    target_date_utc = target_date.astimezone(pytz.utc)
    start_time = int(target_date_utc.timestamp() * 1000)  # Convert to milliseconds
    
    try:
        open_price = get_binance_price(symbol, interval, start_time)
        close_price = get_binance_price(symbol, interval, start_time + 3600000)  # Next hour candle
        
        open_price = float(open_price)
        close_price = float(close_price)
        
        if close_price >= open_price:
            logger.info("Market resolves to Up.")
            return "recommendation: p2"  # Up
        else:
            logger.info("Market resolves to Down.")
            return "recommendation: p1"  # Down
    except Exception as e:
        logger.error(f"Failed to resolve market: {e}")
        return "recommendation: p3"  # Unknown/50-50 if data retrieval fails

if __name__ == "__main__":
    result = resolve_market()
    print(result)