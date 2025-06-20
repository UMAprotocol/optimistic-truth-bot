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
    Fetches the price data from Binance API for a given symbol and interval at a specific start time.
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
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price of the candle
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}")
            raise

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance at a specific time.
    """
    # Define the specific time and date
    target_date = datetime(2025, 6, 10, 18, 0, 0, tzinfo=pytz.timezone('US/Eastern'))  # June 10, 6 PM ET
    target_timestamp = int(target_date.timestamp() * 1000)  # Convert to milliseconds
    
    try:
        # Get the closing price at the start of the 1 hour candle
        start_price = get_binance_price("BTCUSDT", "1h", target_timestamp)
        # Get the closing price at the end of the 1 hour candle
        end_price = get_binance_price("BTCUSDT", "1h", target_timestamp + 3600000)
        
        # Determine if the price went up or down
        if end_price >= start_price:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logger.error(f"Failed to resolve market: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    resolve_market()