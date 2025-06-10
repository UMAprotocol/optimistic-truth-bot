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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_binance_data(symbol, start_time):
    """
    Fetches the 1-hour candle data for a cryptocurrency pair on Binance at a specific start time.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        start_time: Start time in milliseconds for the 1-hour candle

    Returns:
        JSON response containing candle data
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour in milliseconds
    }

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(primary_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_date):
    """
    Resolves the market based on the price change of the specified symbol on the target date.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        target_date: Target date in "YYYY-MM-DD" format

    Returns:
        Recommendation based on the price change
    """
    # Convert date to the start of the 9 AM ET hour in UTC milliseconds
    tz = pytz.timezone("US/Eastern")
    naive_datetime = datetime.strptime(target_date + " 09:00:00", "%Y-%m-%d %H:%M:%S")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    start_time_ms = int(utc_datetime.timestamp() * 1000)

    # Get data from Binance
    data = get_binance_data(symbol, start_time_ms)
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = close_price - open_price

        # Determine resolution based on price change
        if price_change >= 0:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    """
    Main function to handle the resolution of the market.
    """
    try:
        result = resolve_market("BTCUSDT", "2025-05-29")
        print(result)
    except Exception as e:
        logging.error(f"Error resolving market: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()