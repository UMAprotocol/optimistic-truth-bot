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

def get_binance_price(symbol, target_time):
    """
    Fetches the closing price of a cryptocurrency at a specific time from Binance.
    
    Args:
        symbol (str): The symbol of the cryptocurrency pair (e.g., 'BTCUSDT').
        target_time (datetime): The target datetime object in UTC.
    
    Returns:
        float: The closing price of the cryptocurrency.
    """
    # Convert datetime to milliseconds since epoch
    target_time_ms = int(target_time.timestamp() * 1000)
    
    # URLs for Binance API
    primary_url = "https://api.binance.com/api/v3/klines"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    
    # Parameters for the API call
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": target_time_ms,
        "endTime": target_time_ms + 60000  # 1 minute later
    }
    
    try:
        # Try using the proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Closing price
    except Exception as e:
        logger.error(f"Proxy failed, error: {e}. Trying primary endpoint.")
        # Fallback to the primary endpoint if proxy fails
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Closing price
        except Exception as e:
            logger.error(f"Primary endpoint also failed, error: {e}")
            raise

def main():
    # Define the target time and symbol
    target_time_str = "2025-06-06 12:00:00"
    symbol = "BTCUSDT"
    timezone_str = "US/Eastern"
    
    # Convert target time to UTC
    tz = pytz.timezone(timezone_str)
    target_time = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
    target_time = tz.localize(target_time).astimezone(pytz.utc)
    
    try:
        # Get the closing price from Binance
        closing_price = get_binance_price(symbol, target_time)
        logger.info(f"Closing price for {symbol} at {target_time_str} {timezone_str} is {closing_price}")
        
        # Determine the resolution based on the closing price
        if closing_price >= 111000.01:
            print("recommendation: p2")  # Yes
        else:
            print("recommendation: p1")  # No
    except Exception as e:
        logger.error(f"Failed to retrieve data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()