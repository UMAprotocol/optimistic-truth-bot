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

def fetch_binance_data(symbol, interval, start_time, end_time, proxy_url, primary_url):
    """
    Fetches data from Binance using a proxy and falls back to the primary endpoint if necessary.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(primary_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the open and close price for a specific 1-hour candle on Binance.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Binance API endpoints
    primary_url = "https://api.binance.com/api/v3/klines"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

    # Fetch data
    data = fetch_binance_data(symbol, "1h", start_time, end_time, proxy_url, primary_url)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        raise ValueError("No data returned from Binance for the specified time and symbol.")

def resolve_market(open_price, close_price):
    """
    Resolves the market based on the open and close prices.
    """
    if close_price >= open_price:
        return "p2"  # Up
    else:
        return "p1"  # Down

def main():
    """
    Main function to resolve the market for Solana on Binance.
    """
    try:
        # Define the target date and time
        target_datetime = datetime(2025, 6, 19, 3, 0, tzinfo=pytz.timezone("US/Eastern"))
        symbol = "SOLUSDT"

        # Get the open and close prices for the specified candle
        open_price, close_price = get_candle_data(symbol, target_datetime)

        # Resolve the market based on the prices
        resolution = resolve_market(open_price, close_price)
        print(f"recommendation: {resolution}")
    except Exception as e:
        logger.error(f"Error resolving market: {e}")
        print("recommendation: p4")  # Unknown or error

if __name__ == "__main__":
    main()