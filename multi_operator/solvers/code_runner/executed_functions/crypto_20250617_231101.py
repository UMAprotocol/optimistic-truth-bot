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
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def fetch_candle_data(symbol, interval, start_time):
    """
    Fetches candle data for a given symbol and interval from Binance API.
    Args:
        symbol (str): The symbol to fetch data for.
        interval (str): The interval of the candle data.
        start_time (int): The start time in milliseconds for the candle data.
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
        # Try fetching from proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to primary endpoint
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}")
            raise

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the open and close prices of the candle.
    Args:
        symbol (str): The symbol to check.
        target_datetime (datetime): The datetime for which to check the price.
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
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    # Example: Solana on June 17, 2025, 6PM ET
    target_datetime = datetime(2025, 6, 17, 18, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "SOLUSDT"
    try:
        result = resolve_market(symbol, target_datetime)
        print(result)
    except Exception as e:
        logger.error(f"Error resolving market: {e}")
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()