import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def fetch_price_data(symbol, start_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }
    
    try:
        # Try fetching from proxy first
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy.")
    except Exception as e:
        logger.error(f"Failed to fetch data from proxy: {e}. Trying primary API.")
        # Fallback to primary API
        try:
            response = requests.get(PRIMARY_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary API.")
        except Exception as e:
            logger.error(f"Failed to fetch data from primary API: {e}")
            return None

    if data and len(data) > 0:
        return data[0]  # Return the first (and only) candle
    return None

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price data of the specified symbol at the target datetime.
    """
    # Convert datetime to milliseconds since epoch
    target_timestamp = int(target_datetime.timestamp() * 1000)
    
    # Fetch price data
    price_data = fetch_price_data(symbol, target_timestamp)
    
    if price_data:
        open_price = float(price_data[1])
        close_price = float(price_data[4])
        
        # Determine resolution based on price comparison
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50 if no data available

def main():
    # Example usage
    symbol = "SOLUSDT"
    target_datetime_str = "2025-06-17 20:00:00"
    timezone_str = "America/New_York"
    
    # Convert string to datetime object in the specified timezone
    timezone = pytz.timezone(timezone_str)
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = timezone.localize(target_datetime)
    
    # Resolve the market
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()