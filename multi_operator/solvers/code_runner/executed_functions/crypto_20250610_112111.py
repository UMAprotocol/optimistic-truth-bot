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
    Fetches the close price of a cryptocurrency from Binance at a specific start time.
    
    Args:
        symbol (str): The symbol to fetch, e.g., 'BTCUSDT'
        start_time (int): The start time in milliseconds since the epoch (UTC)
    
    Returns:
        float: The close price of the cryptocurrency
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
            return float(data[0][4])  # Close price
    except Exception as e:
        logger.error(f"Proxy failed with error: {e}, trying primary endpoint.")
        # Fallback to primary endpoint
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price
        except Exception as e:
            logger.error(f"Primary endpoint also failed with error: {e}")
            raise

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance.
    """
    target_date = datetime(2025, 6, 10, 5, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    target_date_utc = target_date.astimezone(pytz.utc)
    start_time_ms = int(target_date_utc.timestamp() * 1000)
    
    try:
        close_price = get_binance_price("BTCUSDT", start_time_ms)
        logger.info(f"Close price for BTC/USDT at {target_date.strftime('%Y-%m-%d %H:%M:%S %Z')} is {close_price}")
        
        # Assuming we need to compare with the previous hour's close price
        previous_close_price = get_binance_price("BTCUSDT", start_time_ms - 3600000)
        
        if close_price >= previous_close_price:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logger.error(f"Failed to resolve market due to error: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    resolve_market()