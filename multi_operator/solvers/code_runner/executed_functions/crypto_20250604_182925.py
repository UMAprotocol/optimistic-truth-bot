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
        target_time (datetime): The target datetime in UTC.
    
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
        # Try fetching data from the proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        logger.error(f"Proxy failed, error: {e}, trying primary endpoint.")
        # If proxy fails, fallback to the primary endpoint
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            close_price = float(data[0][4])
            return close_price
        except Exception as e:
            logger.error(f"Primary endpoint also failed, error: {e}")
            raise

def main():
    # Define the target date and time
    target_date_str = "2025-05-16"
    target_time = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_time = pytz.timezone("US/Eastern").localize(target_time.replace(hour=12, minute=0))
    target_time_utc = target_time.astimezone(pytz.utc)
    
    # Symbol for the cryptocurrency
    symbol = "BTCUSDT"
    
    try:
        # Get the closing price from Binance
        close_price = get_binance_price(symbol, target_time_utc)
        logger.info(f"Close price for {symbol} at {target_date_str} 12:00 ET is {close_price}")
        
        # Determine the resolution based on the close price
        if close_price >= 108000.01:
            print("recommendation: p2")  # Yes
        else:
            print("recommendation: p1")  # No
    except Exception as e:
        logger.error(f"Failed to fetch price data: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()