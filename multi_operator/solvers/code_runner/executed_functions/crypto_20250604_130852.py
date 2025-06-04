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
    Fetches the closing price of a cryptocurrency from Binance for a specific 1-hour candle.
    
    Args:
        symbol (str): The symbol to fetch, e.g., 'BTCUSDT'
        start_time (int): The start time of the candle in milliseconds since epoch UTC
    
    Returns:
        float: The closing price of the candle
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"
    
    params = {
        "symbol": symbol,
        "interval": "1h",
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
            return float(data[0][4])  # Closing price
    except Exception as e:
        logger.error(f"Proxy failed, trying primary endpoint: {e}")
        try:
            # Fallback to primary endpoint
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Closing price
        except Exception as e:
            logger.error(f"Both proxy and primary endpoints failed: {e}")
            raise

def resolve_market():
    """
    Resolves the market based on the BTC/USDT price change on Binance.
    """
    symbol = "BTCUSDT"
    target_date = datetime(2025, 5, 31, 10, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    target_date_utc = target_date.astimezone(pytz.utc)
    start_time_ms = int(target_date_utc.timestamp() * 1000)
    
    try:
        closing_price_start = get_binance_price(symbol, start_time_ms)
        logger.info(f"Closing price at start: {closing_price_start}")
        
        # Check the price after one hour
        closing_price_end = get_binance_price(symbol, start_time_ms + 3600000)
        logger.info(f"Closing price at end: {closing_price_end}")
        
        if closing_price_end >= closing_price_start:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    except Exception as e:
        logger.error(f"Error resolving market: {e}")
        return "recommendation: p3"  # Unknown/50-50

if __name__ == "__main__":
    result = resolve_market()
    print(result)