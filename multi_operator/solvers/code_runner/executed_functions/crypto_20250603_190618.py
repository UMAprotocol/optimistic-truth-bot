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
PRIMARY_API = "https://api.binance.com/api/v3"
PROXY_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching from proxy first
        response = requests.get(f"{PROXY_API}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logging.error(f"Proxy failed with error: {e}. Trying primary API.")
        # Fallback to primary API
        response = requests.get(f"{PRIMARY_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from primary API.")
        return data

def get_candle_data(symbol, target_datetime):
    """
    Converts the target datetime to UTC and fetches the 1-hour candle data for that period.
    """
    # Convert target datetime to UTC timestamp
    utc_datetime = target_datetime.astimezone(pytz.utc)
    start_time = int(utc_datetime.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # Fetch the candle data
    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    else:
        raise ValueError("No data returned from API.")

def resolve_market(target_datetime_str, symbol="BTCUSDT"):
    """
    Resolves the market based on the price movement of the specified symbol at the given datetime.
    """
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.timezone("US/Eastern"))
    try:
        open_price, close_price = get_candle_data(symbol, target_datetime)
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    except Exception as e:
        logging.error(f"Error resolving market: {e}")
        return "recommendation: p3"  # Unknown/50-50

def main():
    # Example usage
    result = resolve_market("2025-06-03 14:00:00")
    print(result)

if __name__ == "__main__":
    main()