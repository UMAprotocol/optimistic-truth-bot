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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_candle_data(symbol, interval, start_time, end_time):
    """
    Fetches candle data for the specified symbol and interval from Binance API.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logging.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint.")
        # Fallback to the primary endpoint
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logging.error(f"Primary endpoint also failed: {e}")
            raise

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the opening and closing prices of the candle.
    """
    # Convert target time to UTC timestamp
    et_timezone = pytz.timezone('US/Eastern')
    target_datetime = et_timezone.localize(datetime.strptime(target_time, '%Y-%m-%d %H:%M'))
    target_timestamp = int(target_datetime.timestamp() * 1000)

    # Fetch candle data
    data = fetch_candle_data(symbol, "1h", target_timestamp, target_timestamp + 3600000)

    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50

def main():
    """
    Main function to handle the resolution of the market.
    """
    try:
        result = resolve_market("SOLUSDT", "2025-06-19 19:00")
        print(f"recommendation: {result}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Default to unknown if there's an error

if __name__ == "__main__":
    main()