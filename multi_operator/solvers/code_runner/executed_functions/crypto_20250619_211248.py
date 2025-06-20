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

def fetch_binance_data(symbol, interval, start_time, end_time, proxy_first=True):
    """
    Fetches data from Binance API with a fallback mechanism from proxy to primary endpoint.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    urls = [proxy_url, primary_url] if proxy_first else [primary_url, proxy_url]
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }

    for url in urls:
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]  # Return the first (and only) candle
        except Exception as e:
            logger.error(f"Failed to fetch data from {url}: {str(e)}")
            continue
    raise Exception("Failed to retrieve data from all endpoints.")

def resolve_market():
    """
    Resolves the market based on the SOL/USDT pair price data from Binance.
    """
    # Define the specific date and time for the event
    event_datetime = datetime(2025, 6, 19, 16, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    event_timestamp = int(event_datetime.timestamp() * 1000)  # Convert to milliseconds

    try:
        # Fetch the 1-hour candle data for SOL/USDT starting at the event time
        candle_data = fetch_binance_data("SOLUSDT", "1h", event_timestamp, event_timestamp + 3600000)
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])

        # Determine the resolution based on the close and open prices
        if close_price >= open_price:
            recommendation = "p2"  # Up
        else:
            recommendation = "p1"  # Down

        logger.info(f"Market resolved with recommendation: {recommendation}")
        print(f"recommendation: {recommendation}")
    except Exception as e:
        logger.error(f"Error resolving market: {str(e)}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    resolve_market()