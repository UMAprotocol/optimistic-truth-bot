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

def fetch_price_data(symbol, interval, start_time):
    """
    Fetches price data from Binance using the proxy endpoint with a fallback to the primary endpoint.
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
        # Try fetching data from the proxy endpoint
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data[0]
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to the primary endpoint
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data[0]
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}")
            raise

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the specified symbol at the target time.
    """
    # Convert target time to UTC milliseconds
    target_time_utc = int(target_time.timestamp() * 1000)
    
    # Fetch the price data for the specified hour
    candle_data = fetch_price_data(symbol, "1h", target_time_utc)
    
    # Calculate the percentage change
    open_price = float(candle_data[1])
    close_price = float(candle_data[4])
    percent_change = ((close_price - open_price) / open_price) * 100
    
    # Determine the resolution based on the percentage change
    if percent_change >= 0:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to handle the resolution of the Ethereum Up or Down market.
    """
    # Define the target time for the market resolution
    target_time_str = "2025-06-16 20:00:00"
    timezone_str = "US/Eastern"
    
    # Convert the target time to a datetime object
    tz = pytz.timezone(timezone_str)
    target_time = tz.localize(datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S"))
    
    # Resolve the market
    resolution = resolve_market("ETHUSDT", target_time)
    
    # Output the recommendation
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()