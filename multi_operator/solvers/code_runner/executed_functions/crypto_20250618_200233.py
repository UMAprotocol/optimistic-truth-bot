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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# API endpoints
PRIMARY_API = "https://api.binance.com/api/v3"
PROXY_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

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
        response = requests.get(f"{PROXY_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy.")
    except Exception as e:
        logger.error(f"Proxy failed with error: {e}. Trying primary API.")
        try:
            # Fallback to primary API
            response = requests.get(f"{PRIMARY_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary API.")
        except Exception as e:
            logger.error(f"Primary API failed with error: {e}.")
            return None

    if data:
        return data[0]  # Return the first (and only) candle
    return None

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price data fetched.
    """
    # Convert target time to UTC timestamp
    utc_time = int(target_time.replace(tzinfo=pytz.timezone("US/Eastern")).timestamp() * 1000)
    
    # Fetch price data
    data = fetch_price_data(symbol, utc_time)
    if data:
        open_price = float(data[1])
        close_price = float(data[4])
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    return "recommendation: p3"  # Unknown/50-50 if data is not available

def main():
    # Example: June 18, 2025, 3 PM ET
    target_time = datetime(2025, 6, 18, 15, 0, 0)
    symbol = "BTCUSDT"
    result = resolve_market(symbol, target_time)
    print(result)

if __name__ == "__main__":
    main()