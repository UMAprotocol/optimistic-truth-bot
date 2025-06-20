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
    raise Exception("Both primary and proxy endpoints failed.")

def resolve_market():
    """
    Resolves the market based on the BTC/USDT price change on Binance.
    """
    symbol = "BTCUSDT"
    interval = "1h"
    target_time = datetime(2025, 6, 13, 18, 0, tzinfo=pytz.timezone("US/Eastern"))
    target_time_utc = target_time.astimezone(pytz.utc)
    start_time = int(target_time_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    try:
        candle = get_binance_data(symbol, interval, start_time, end_time)
        open_price = float(candle[1])
        close_price = float(candle[4])
        price_change = (close_price - open_price) / open_price * 100

        if price_change >= 0:
            recommendation = "p2"  # Up
        else:
            recommendation = "p1"  # Down

        logger.info(f"Market resolved: {recommendation} (Price change: {price_change:.2f}%)")
        return recommendation
    except Exception as e:
        logger.error(f"Error resolving market: {str(e)}")
        return "p3"  # Unknown/50-50 if error occurs

def main():
    """
    Main function to execute the market resolution.
    """
    result = resolve_market()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()