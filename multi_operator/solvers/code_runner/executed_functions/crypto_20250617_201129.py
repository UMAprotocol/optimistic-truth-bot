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

def fetch_price_from_binance(symbol, start_time):
    """
    Fetches the closing price of a cryptocurrency from Binance at a specific start time.
    Args:
        symbol (str): The symbol of the cryptocurrency to fetch.
        start_time (int): The start time in milliseconds since the epoch.
    Returns:
        float: The closing price of the cryptocurrency.
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
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Closing price
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}")
            raise

def resolve_market():
    """
    Resolves the market based on the price change of ETH/USDT on Binance.
    """
    symbol = "ETHUSDT"
    target_time = datetime(2025, 6, 17, 15, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    target_time_utc = target_time.astimezone(pytz.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)

    try:
        closing_price = fetch_price_from_binance(symbol, start_time_ms)
        logger.info(f"Closing price for {symbol} at {target_time.strftime('%Y-%m-%d %H:%M:%S %Z')} is {closing_price}")
        if closing_price >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logger.error(f"Failed to fetch price data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if data fetch fails

if __name__ == "__main__":
    resolve_market()