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
    Fetches price data from Binance using either the proxy or primary endpoint.
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
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price of the candle
    except Exception as e:
        logger.error(f"Proxy failed, trying primary endpoint: {e}")
        try:
            # Fallback to primary endpoint
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price of the candle
        except Exception as e:
            logger.error(f"Both proxy and primary endpoints failed: {e}")
            raise

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance.
    """
    symbol = "BTCUSDT"
    interval = "1h"
    target_time_str = "2025-06-10 01:00:00"
    timezone_str = "US/Eastern"
    
    # Convert target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    target_time = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
    target_time = tz.localize(target_time).astimezone(pytz.utc)
    start_time_ms = int(target_time.timestamp() * 1000)
    
    try:
        # Get the closing price at the start and end of the interval
        start_price = get_binance_price(symbol, interval, start_time_ms)
        end_price = get_binance_price(symbol, interval, start_time_ms + 3600000)
        
        # Determine market resolution
        if end_price >= start_price:
            logger.info("Market resolves to 'Up'")
            return "recommendation: p2"  # Up
        else:
            logger.info("Market resolves to 'Down'")
            return "recommendation: p1"  # Down
    except Exception as e:
        logger.error(f"Failed to resolve market: {e}")
        return "recommendation: p3"  # Unknown/50-50

if __name__ == "__main__":
    result = resolve_market()
    print(result)