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
    Fetches price data from Binance API with a fallback to a proxy endpoint.
    """
    primary_url = "https://api.binance.com/api/v3/klines"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }
    
    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price of the candle
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price of the candle
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}")
            raise

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance.
    """
    symbol = "BTCUSDT"
    interval = "1h"
    target_time_str = "2025-06-12 05:00:00"
    timezone_str = "US/Eastern"
    
    # Convert target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    target_time = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
    target_time = tz.localize(target_time).astimezone(pytz.utc)
    start_time_ms = int(target_time.timestamp() * 1000)
    
    try:
        initial_price = get_binance_price(symbol, interval, start_time_ms)
        logger.info(f"Initial price at {target_time_str}: {initial_price}")
        
        # Assuming we need to compare with the price one hour later
        final_price = get_binance_price(symbol, interval, start_time_ms + 3600000)
        logger.info(f"Final price one hour later: {final_price}")
        
        if final_price >= initial_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    except Exception as e:
        logger.error(f"Failed to resolve market: {e}")
        return "recommendation: p3"  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    result = resolve_market()
    print(result)