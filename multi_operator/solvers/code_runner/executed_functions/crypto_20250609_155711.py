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
    raise Exception("Failed to fetch data from all endpoints.")

def resolve_market():
    """
    Resolves the market based on the change in price for the BTC/USDT pair on Binance.
    """
    # Define the date and time for the candle
    target_date = datetime(2025, 5, 28, 16, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    start_time = int(target_date.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch the close price at the start and end of the candle
    try:
        start_price = get_binance_data('BTCUSDT', '1h', start_time, start_time + 60000)  # 1 minute after start
        end_price = get_binance_data('BTCUSDT', '1h', end_time - 60000, end_time)  # 1 minute before end

        # Determine the resolution based on the price change
        if end_price >= start_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    except Exception as e:
        logger.error(f"Error resolving market: {str(e)}")
        return "recommendation: p3"  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    result = resolve_market()
    print(result)