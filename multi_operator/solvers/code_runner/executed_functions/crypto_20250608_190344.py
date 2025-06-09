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
        start_time (int): The start time of the candle in milliseconds since epoch

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
        logger.error(f"Proxy failed, error: {e}. Trying primary endpoint.")
        try:
            # Fallback to primary endpoint
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Closing price
        except Exception as e:
            logger.error(f"Both endpoints failed, error: {e}")
            raise

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance.
    """
    symbol = "BTCUSDT"
    et_timezone = pytz.timezone("US/Eastern")
    target_date = datetime(2025, 6, 8, 14, 0, 0, tzinfo=et_timezone)  # June 8, 2025, 2 PM ET
    start_time_utc = target_date.astimezone(pytz.utc)
    start_time_ms = int(start_time_utc.timestamp() * 1000)

    try:
        closing_price = get_binance_price(symbol, start_time_ms)
        logger.info(f"Closing price for {symbol} at {target_date.strftime('%Y-%m-%d %H:%M %Z')} is {closing_price}")
        return "recommendation: p2" if closing_price < 0 else "recommendation: p1"
    except Exception as e:
        logger.error(f"Failed to resolve market due to error: {e}")
        return "recommendation: p3"

if __name__ == "__main__":
    result = resolve_market()
    print(result)