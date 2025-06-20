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
    Fetches the closing price of a cryptocurrency from Binance at a specific start time.
    
    Args:
        symbol (str): The symbol to fetch, e.g., 'BTCUSDT'
        start_time (int): The start time in milliseconds since the epoch (UTC)
    
    Returns:
        float: The closing price of the cryptocurrency
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
        logger.error(f"Proxy failed, error: {e}, trying primary endpoint")
        try:
            # Fallback to primary endpoint
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Closing price
        except Exception as e:
            logger.error(f"Primary endpoint also failed, error: {e}")
            raise

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance.
    """
    symbol = "BTCUSDT"
    target_time_str = "2025-06-10 11:00:00"
    timezone_str = "US/Eastern"
    
    # Convert target time to UTC
    tz = pytz.timezone(timezone_str)
    target_time = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
    target_time = tz.localize(target_time).astimezone(pytz.utc)
    start_time_ms = int(target_time.timestamp() * 1000)
    
    try:
        price_start = get_binance_price(symbol, start_time_ms)
        price_end = get_binance_price(symbol, start_time_ms + 3600000)  # 1 hour later
        
        if price_end >= price_start:
            recommendation = "p2"  # Up
        else:
            recommendation = "p1"  # Down
        
        print(f"recommendation: {recommendation}")
    except Exception as e:
        logger.error(f"Failed to resolve market: {e}")
        print("recommendation: p3")  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    resolve_market()