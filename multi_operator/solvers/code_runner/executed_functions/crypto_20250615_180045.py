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
    Fetches the price of a cryptocurrency from Binance at a specific start time.
    
    Args:
        symbol (str): The symbol of the cryptocurrency to fetch.
        start_time (int): The start time in milliseconds for the 1-hour candle.
    
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
        "endTime": start_time + 3600000  # 1 hour in milliseconds
    }
    
    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Closing price
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to the primary endpoint if proxy fails
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Closing price
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}")
            raise

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of a cryptocurrency.
    
    Args:
        symbol (str): The symbol of the cryptocurrency.
        target_time (datetime): The target datetime object in UTC.
    
    Returns:
        str: The resolution of the market ('p1' for Down, 'p2' for Up, 'p3' for unknown).
    """
    start_time_ms = int(target_time.timestamp() * 1000)
    closing_price = fetch_price_from_binance(symbol, start_time_ms)
    
    # Assuming we have the previous closing price to compare against
    # This is a simplification, in a real scenario we would fetch this from another API call
    previous_closing_price = fetch_price_from_binance(symbol, start_time_ms - 3600000)
    
    if closing_price >= previous_closing_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    # Example usage
    target_time = datetime(2025, 6, 15, 17, 0, 0, tzinfo=timezone.utc)  # 1 PM ET in UTC
    symbol = "ETHUSDT"
    try:
        result = resolve_market(symbol, target_time)
        print(f"recommendation: {result}")
    except Exception as e:
        logger.error(f"Failed to resolve market: {e}")
        print("recommendation: p3")  # Unknown if there's an error

if __name__ == "__main__":
    main()