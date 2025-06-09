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
    Fetches price data from Binance API for a given symbol and interval.
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
        return float(data[0][4])  # Close price
    except Exception as e:
        logger.error(f"Proxy failed, trying primary endpoint: {e}")
        # Fallback to primary endpoint
        try:
            response = requests.get(primary_url, params=params)
            response.raise_for_status()
            data = response.json()
            return float(data[0][4])  # Close price
        except Exception as e:
            logger.error(f"Both proxy and primary endpoints failed: {e}")
            raise

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance.
    """
    symbol = "BTCUSDT"
    interval = "1h"
    # Convert 4 AM ET to UTC timestamp
    et_timezone = pytz.timezone("US/Eastern")
    target_time = et_timezone.localize(datetime(2025, 6, 7, 4, 0, 0))
    target_time_utc = target_time.astimezone(pytz.utc)
    start_time = int(target_time_utc.timestamp() * 1000)
    
    try:
        open_price = get_binance_price(symbol, interval, start_time)
        close_price = get_binance_price(symbol, interval, start_time + 3600000)  # Next hour's candle
        price_change = close_price - open_price
        recommendation = "p2" if price_change < 0 else "p1"
        logger.info(f"Market resolved: {recommendation} (Open: {open_price}, Close: {close_price})")
        return recommendation
    except Exception as e:
        logger.error(f"Failed to resolve market: {e}")
        return "p4"  # Unable to resolve

if __name__ == "__main__":
    result = resolve_market()
    print(f"recommendation: {result}")