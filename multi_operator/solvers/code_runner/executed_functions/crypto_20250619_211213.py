import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_candle_data(symbol, interval, start_time):
    """
    Fetches candle data for a given symbol and interval from Binance API.
    Args:
        symbol (str): The symbol to fetch data for.
        interval (str): The interval of the candle data.
        start_time (int): The start time for the data in milliseconds.
    Returns:
        dict: The candle data.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }
    try:
        # Try fetching from proxy first
        response = requests.get(f"{PROXY_API_URL}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        logging.warning(f"Proxy failed with error: {e}. Trying primary API.")
        # Fallback to primary API if proxy fails
        try:
            response = requests.get(f"{PRIMARY_API_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            logging.error(f"Primary API failed with error: {e}")
            raise ConnectionError("Failed to fetch data from both proxy and primary APIs.")

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the opening and closing prices of the specified symbol at the target datetime.
    Args:
        symbol (str): The symbol to check.
        target_datetime (datetime): The datetime for which to check the prices.
    Returns:
        str: The resolution of the market.
    """
    # Convert datetime to UTC timestamp in milliseconds
    utc_datetime = target_datetime.astimezone(pytz.utc)
    start_time_ms = int(utc_datetime.timestamp() * 1000)

    # Fetch candle data
    candle_data = fetch_candle_data(symbol, "1h", start_time_ms)
    if candle_data:
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])

        # Determine market resolution
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    # Example: Solana on June 19, 2025, 4PM ET
    target_datetime = datetime(2025, 6, 19, 16, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "SOLUSDT"
    try:
        result = resolve_market(symbol, target_datetime)
        print(result)
    except Exception as e:
        logging.error(f"Error resolving market: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()