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
        start_time (datetime): The start time of the 1-hour candle in UTC
    
    Returns:
        float: The closing price of the candle
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"
    
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": int(start_time.timestamp() * 1000),  # Convert to milliseconds
        "endTime": int((start_time + timedelta(hours=1)).timestamp() * 1000)
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
    Main function to determine if the price of BTC/USDT went up or down at a specific time.
    """
    symbol = "BTCUSDT"
    target_time_str = "2025-06-04 20:00:00"
    target_timezone = "US/Eastern"
    
    # Convert target time to UTC
    target_time = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
    eastern = pytz.timezone(target_timezone)
    target_time = eastern.localize(target_time).astimezone(pytz.utc)
    
    try:
        closing_price_start = get_binance_price(symbol, target_time)
        closing_price_end = get_binance_price(symbol, target_time + timedelta(hours=1))
        
        if closing_price_end >= closing_price_start:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logger.error(f"Failed to fetch prices: {e}")
        print("recommendation: p3")  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    main()