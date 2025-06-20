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
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_candle_data(symbol, interval, start_time, end_time):
    """
    Fetches candle data for a given symbol and interval from Binance API.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }
    try:
        # Try fetching from proxy first
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        logging.warning(f"Proxy failed with error: {e}. Trying primary API.")
        # Fallback to primary API if proxy fails
        try:
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            logging.error(f"Primary API also failed with error: {e}")
            raise

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of the symbol at the specified datetime.
    """
    # Convert datetime to UTC timestamp in milliseconds
    utc_datetime = target_datetime.astimezone(pytz.utc)
    start_time = int(utc_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch candle data
    candle = fetch_candle_data(symbol, "1h", start_time, end_time)
    if candle:
        open_price = float(candle[1])
        close_price = float(candle[4])
        change_percentage = ((close_price - open_price) / open_price) * 100

        # Determine resolution based on price change
        if change_percentage >= 0:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    # Example: Ethereum on June 11, 2025, 7 AM ET
    target_datetime = datetime(2025, 6, 11, 7, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "ETHUSDT"
    try:
        result = resolve_market(symbol, target_datetime)
        print(result)
    except Exception as e:
        logging.error(f"Failed to resolve market due to: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()