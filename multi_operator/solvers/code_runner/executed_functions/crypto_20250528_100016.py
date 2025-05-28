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

def get_binance_data(symbol, interval, start_time, end_time, proxy_first=True):
    """
    Fetches data from Binance API with a fallback mechanism from proxy to primary endpoint.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    urls = [(proxy_url, {'symbol': symbol, 'interval': interval, 'limit': 1, 'startTime': start_time, 'endTime': end_time}),
            (primary_url, {'symbol': symbol, 'interval': interval, 'limit': 1, 'startTime': start_time, 'endTime': end_time})]

    if not proxy_first:
        urls.reverse()

    for url, params in urls:
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price of the candle
        except Exception as e:
            logger.error(f"Failed to fetch data from {url}: {str(e)}")
            continue
    raise Exception("Both primary and proxy endpoints failed.")

def resolve_market():
    """
    Resolves the market based on the change in price for the BTC/USDT pair on Binance.
    """
    symbol = "BTCUSDT"
    interval = "1h"
    et_timezone = pytz.timezone("US/Eastern")
    utc_timezone = pytz.timezone("UTC")

    # Define the specific date and time for the candle
    target_date = datetime(2025, 5, 28, 5, 0, 0, tzinfo=et_timezone)
    start_time_utc = target_date.astimezone(utc_timezone)
    end_time_utc = start_time_utc + timedelta(hours=1)

    start_time_ms = int(start_time_utc.timestamp() * 1000)
    end_time_ms = int(end_time_utc.timestamp() * 1000)

    try:
        close_price_start = get_binance_data(symbol, interval, start_time_ms, start_time_ms + 60000)
        close_price_end = get_binance_data(symbol, interval, end_time_ms - 60000, end_time_ms)
        price_change = close_price_end - close_price_start

        if price_change >= 0:
            recommendation = "p2"  # Up
        else:
            recommendation = "p1"  # Down

        return recommendation
    except Exception as e:
        logger.error(f"Error resolving market: {str(e)}")
        return "p3"  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    result = resolve_market()
    print(f"recommendation: {result}")