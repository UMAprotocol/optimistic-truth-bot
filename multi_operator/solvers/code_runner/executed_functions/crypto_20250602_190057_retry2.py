import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def fetch_binance_data(symbol, interval, startTime, endTime, use_proxy=False):
    """
    Fetches data from Binance API.
    Args:
        symbol (str): The symbol to fetch data for.
        interval (str): The interval of the data.
        startTime (int): Start time in milliseconds.
        endTime (int): End time in milliseconds.
        use_proxy (bool): Whether to use the proxy endpoint.
    Returns:
        dict: The API response.
    """
    url = PROXY_BINANCE_API if use_proxy else PRIMARY_BINANCE_API
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": startTime,
        "endTime": endTime,
        "limit": 1
    }
    try:
        response = requests.get(f"{url}/klines", params=params)
        response.raise_for_status()
        data = response.json()
        return data[0]  # Return the first (and only) entry
    except requests.RequestException as e:
        if not use_proxy:
            logger.error("Failed to fetch data from primary, no fallback available.")
            raise
        else:
            logger.info("Proxy failed, falling back to primary endpoint.")
            return fetch_binance_data(symbol, interval, startTime, endTime, use_proxy=False)

def resolve_market(symbol, target_date_time):
    """
    Resolves the market based on the price change of the symbol at the specified date and time.
    Args:
        symbol (str): The symbol to check.
        target_date_time (datetime): The datetime to check.
    Returns:
        str: The market resolution.
    """
    # Convert target datetime to UTC timestamp in milliseconds
    utc_time = target_date_time.astimezone(pytz.utc)
    start_time = int(utc_time.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch data
    data = fetch_binance_data(symbol, "1h", start_time, end_time, use_proxy=True)
    open_price = float(data[1])
    close_price = float(data[4])

    # Determine market resolution
    if close_price >= open_price:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

def main():
    # Example usage
    target_date_str = "2025-06-02"
    target_time_str = "14:00:00"
    target_date_time = datetime.strptime(f"{target_date_str} {target_time_str}", "%Y-%m-%d %H:%M:%S")
    target_date_time = pytz.timezone("America/New_York").localize(target_date_time)

    resolution = resolve_market("BTCUSDT", target_date_time)
    print(resolution)

if __name__ == "__main__":
    main()