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
    Args:
        symbol (str): The symbol to fetch data for, e.g., 'BTCUSDT'.
        interval (str): The interval of the candlestick data, e.g., '1h'.
        start_time (int): The start time for the data in milliseconds.
    Returns:
        float: The closing price of the candlestick.
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
    Resolves the market based on the price change of BTC/USDT on Binance.
    """
    symbol = "BTCUSDT"
    interval = "1h"
    target_date = datetime(2025, 5, 28, 23, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    target_date_utc = target_date.astimezone(pytz.utc)
    start_time = int(target_date_utc.timestamp() * 1000)  # Convert to milliseconds

    try:
        closing_price = get_binance_price(symbol, interval, start_time)
        logger.info(f"Closing price for {symbol} at {target_date.strftime('%Y-%m-%d %H:%M:%S %Z')} is {closing_price}")
        return "recommendation: p2" if closing_price < 0 else "recommendation: p1"
    except Exception as e:
        logger.error(f"Failed to resolve market: {e}")
        return "recommendation: p3"

if __name__ == "__main__":
    result = resolve_market()
    print(result)