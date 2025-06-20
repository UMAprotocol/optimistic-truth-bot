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
    Resolves the market based on the BTCUSDT price change for the specified time and date.
    """
    # Define the specific time and date for the market
    target_date = datetime(2025, 6, 11, 12, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    start_time = int(target_date.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # Fetch the close price at the start and end of the interval
    try:
        start_price = get_binance_data('BTCUSDT', '1h', start_time, start_time)
        end_price = get_binance_data('BTCUSDT', '1h', end_time, end_time)
        price_change = (end_price - start_price) / start_price * 100

        # Determine the resolution based on the price change
        if price_change >= 0:
            recommendation = "p2"  # Up
        else:
            recommendation = "p1"  # Down

        logger.info(f"Market resolved: {recommendation} (Price change: {price_change:.2f}%)")
        return recommendation
    except Exception as e:
        logger.error(f"Error resolving market: {str(e)}")
        return "p3"  # Unknown/50-50 if there's an error

def main():
    """
    Main function to execute the market resolution.
    """
    result = resolve_market()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()