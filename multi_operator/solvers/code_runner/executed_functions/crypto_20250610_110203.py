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

def get_data(symbol, interval, start_time, end_time, proxy_url, primary_url):
    """
    Fetches data from Binance API using a proxy and falls back to the primary API if necessary.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}/klines", params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the symbol at the specified target time.
    """
    # Convert target time to UTC timestamp in milliseconds
    target_time_utc = int(target_time.timestamp() * 1000)
    data = get_data(
        symbol=symbol,
        interval="1h",
        start_time=target_time_utc,
        end_time=target_time_utc + 3600000,  # 1 hour later
        proxy_url="https://minimal-ubuntu-production.up.railway.app/binance-proxy",
        primary_url="https://api.binance.com/api/v3"
    )
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    return "p3"  # Unknown/50-50 if no data

def main():
    """
    Main function to handle the resolution of the Bitcoin Up or Down market.
    """
    # Define the target time for the market resolution
    target_time = datetime(2025, 6, 10, 2, 0, tzinfo=pytz.timezone("US/Eastern"))
    result = resolve_market("BTCUSDT", target_time)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()