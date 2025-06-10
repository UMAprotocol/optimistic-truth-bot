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
        logger.error(f"Proxy failed with error: {e}, trying primary endpoint.")
        try:
            # Fallback to primary endpoint
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Closing price
        except Exception as e:
            logger.error(f"Primary endpoint also failed with error: {e}")
            raise

def main():
    """
    Main function to determine if the Bitcoin price went up or down for the specified candle.
    """
    symbol = "BTCUSDT"
    target_date = datetime(2025, 5, 30, 12, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    target_date_utc = target_date.astimezone(pytz.utc)
    start_time_ms = int(target_date_utc.timestamp() * 1000)
    
    try:
        closing_price_start = get_binance_price(symbol, start_time_ms)
        logger.info(f"Closing price at the start of the candle: {closing_price_start}")
        
        # Assuming we need to compare with the previous candle
        previous_candle_start_time_ms = start_time_ms - 3600000  # 1 hour earlier
        closing_price_previous = get_binance_price(symbol, previous_candle_start_time_ms)
        logger.info(f"Closing price at the start of the previous candle: {closing_price_previous}")
        
        if closing_price_start >= closing_price_previous:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logger.error(f"Failed to fetch prices: {e}")
        print("recommendation: p3")  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    main()