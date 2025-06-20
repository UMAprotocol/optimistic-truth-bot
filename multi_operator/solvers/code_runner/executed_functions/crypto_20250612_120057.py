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

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

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
        response = requests.get(f"{PROXY_API_URL}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}. Falling back to primary endpoint.")
        # Fallback to the primary endpoint
        try:
            response = requests.get(f"{PRIMARY_API_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}.")
            raise

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the symbol at the specified target time.
    """
    # Convert target time to UTC milliseconds
    target_time_utc = int(target_time.timestamp() * 1000)
    data = fetch_price_data(symbol, "1h", target_time_utc, target_time_utc + 3600000)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = close_price - open_price
        recommendation = "p2" if price_change < 0 else "p1"
        logger.info(f"Market resolved: {recommendation} (Open: {open_price}, Close: {close_price})")
        return recommendation
    else:
        logger.error("No data available to resolve the market.")
        return "p3"

def main():
    """
    Main function to execute the market resolution.
    """
    # Define the symbol and the specific time for the market resolution
    symbol = "ETHUSDT"
    target_time = datetime(2025, 6, 12, 7, 0, tzinfo=pytz.timezone("US/Eastern"))
    
    try:
        recommendation = resolve_market(symbol, target_time)
        print(f"recommendation: {recommendation}")
    except Exception as e:
        logger.error(f"Failed to resolve the market: {e}")
        print("recommendation: p3")

if __name__ == "__main__":
    main()