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
    timestamp = int(target_time.timestamp() * 1000)
    
    # URLs for Binance API
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"
    
    # Parameters for the API request
    params = {
        'symbol': symbol,
        'interval': '1m',
        'limit': 1,
        'startTime': timestamp,
        'endTime': timestamp + 60000  # 1 minute later
    }
    
    try:
        # Try using the proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        logger.error(f"Proxy failed, error: {e}. Trying primary endpoint.")
        # Fallback to the primary endpoint if proxy fails
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            close_price = float(data[0][4])
            return close_price
        except Exception as e:
            logger.error(f"Both proxy and primary endpoint failed, error: {e}")
            raise

def main():
    # Define the specific date and time for the query
    target_date_str = "2025-05-16"
    target_time_str = "12:00:00"
    timezone_str = "US/Eastern"
    
    # Convert local time to UTC
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(f"{target_date_str} {target_time_str}", "%Y-%m-%d %H:%M:%S")
    local_datetime = tz.localize(naive_datetime)
    target_utc_datetime = local_datetime.astimezone(pytz.utc)
    
    # Symbol for the cryptocurrency pair
    symbol = "BTCUSDT"
    
    try:
        # Get the closing price from Binance
        close_price = get_binance_price(symbol, target_utc_datetime)
        logger.info(f"Close price for {symbol} at {target_utc_datetime} UTC is {close_price}")
        
        # Determine the resolution based on the close price
        if close_price <= 101999.99:
            print("recommendation: p2")  # Yes, price is below $102K
        else:
            print("recommendation: p1")  # No, price is not below $102K
    except Exception as e:
        logger.error(f"Failed to retrieve or process data: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()