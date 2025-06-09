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

def fetch_binance_data(symbol, interval, start_time, end_time, use_proxy=False):
    """
    Fetches data from Binance API.
    Args:
        symbol (str): The symbol to fetch data for.
        interval (str): The interval of the data.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
        use_proxy (bool): Whether to use the proxy endpoint.
    Returns:
        dict: The API response.
    """
    endpoint = PROXY_BINANCE_API if use_proxy else PRIMARY_BINANCE_API
    url = f"{endpoint}/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data[0]  # Return the first (and only) entry
    except requests.RequestException as e:
        if not use_proxy:
            logger.error("Failed to fetch data from primary, no fallback available.")
            raise
        else:
            logger.info("Proxy failed, falling back to primary endpoint.")
            return fetch_binance_data(symbol, interval, start_time, end_time, use_proxy=False)

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of the symbol at the specified datetime.
    Args:
        symbol (str): The trading symbol.
        target_datetime (datetime): The datetime for which to fetch the price.
    Returns:
        str: The resolution of the market.
    """
    # Convert target datetime to UTC and to milliseconds
    target_time_utc = target_datetime.astimezone(pytz.utc)
    start_time = int(target_time_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch data
    initial_data = fetch_binance_data(symbol, "1h", start_time, end_time, use_proxy=True)
    initial_price = float(initial_data[1])  # Open price
    final_price = float(initial_data[4])  # Close price

    # Determine market resolution
    if final_price >= initial_price:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

def main():
    # Example usage
    target_datetime = datetime(2025, 6, 8, 13, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "BTCUSDT"
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()