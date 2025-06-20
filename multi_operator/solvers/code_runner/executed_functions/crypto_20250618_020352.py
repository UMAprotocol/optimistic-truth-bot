import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_ENDPOINT = "https://api.binance.com/api/v3/klines"
PROXY_API_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}. Falling back to primary endpoint.")
        # Fallback to the primary endpoint
        try:
            response = requests.get(PRIMARY_API_ENDPOINT, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Both endpoints failed: {e}")
            raise

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price data of the specified symbol at the target datetime.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch price data
    data = fetch_price_data(symbol, "1h", start_time, end_time)

    # Extract open and close prices
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50

def main():
    # Example: Solana price on June 17, 2025, 9PM ET
    symbol = "SOLUSDT"
    target_datetime_str = "2025-06-17 21:00:00"
    timezone_str = "US/Eastern"

    # Convert string to datetime
    tz = pytz.timezone(timezone_str)
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = tz.localize(target_datetime)

    # Resolve the market
    result = resolve_market(symbol, target_datetime)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()