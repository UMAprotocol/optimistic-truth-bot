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
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data[0][4]  # Close price of the candle
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(primary_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data[0][4]  # Close price of the candle

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of the specified symbol at the given datetime.
    """
    # Convert datetime to UTC timestamp in milliseconds
    target_timestamp = int(target_datetime.replace(tzinfo=timezone.utc).timestamp() * 1000)
    
    # Fetch the closing price at the start and end of the hour
    start_price = float(fetch_price_data(symbol, "1h", target_timestamp))
    end_price = float(fetch_price_data(symbol, "1h", target_timestamp + 3600000))
    
    # Determine if the price went up or down
    if end_price >= start_price:
        return "p2"  # Market resolves to "Up"
    else:
        return "p1"  # Market resolves to "Down"

def main():
    # Example: Ethereum price change on June 16, 2025, 7 PM ET
    target_datetime = datetime(2025, 6, 16, 19, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "ETHUSDT"
    
    try:
        resolution = resolve_market(symbol, target_datetime)
        print(f"recommendation: {resolution}")
    except Exception as e:
        logger.error(f"Error resolving market: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()