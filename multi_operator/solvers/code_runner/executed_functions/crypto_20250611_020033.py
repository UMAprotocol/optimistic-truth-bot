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

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

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
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logger.error(f"Proxy failed, error: {e}. Trying primary API.")
        try:
            # Fallback to the primary API endpoint
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logger.error(f"Primary API failed, error: {e}.")
            raise

def get_candle_data(symbol, target_datetime):
    """
    Retrieves the closing price of a specific 1-hour candle for the given datetime.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(target_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    data = fetch_price_data(symbol, "1h", start_time, end_time)
    if data and len(data) > 0:
        close_price = float(data[0][4])  # Closing price is the fifth element in the list
        return close_price
    else:
        logger.error("No data returned for the specified time.")
        return None

def resolve_market():
    """
    Resolves the market based on the price change of BTC/USDT on Binance at a specific time.
    """
    target_datetime = datetime(2025, 6, 10, 21, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "BTCUSDT"
    close_price_start = get_candle_data(symbol, target_datetime)
    close_price_end = get_candle_data(symbol, target_datetime + timedelta(hours=1))

    if close_price_start is None or close_price_end is None:
        return "recommendation: p4"  # Unable to resolve due to data fetch error

    price_change_percentage = ((close_price_end - close_price_start) / close_price_start) * 100

    if price_change_percentage >= 0:
        return "recommendation: p1"  # Price went up or stayed the same
    else:
        return "recommendation: p2"  # Price went down

if __name__ == "__main__":
    result = resolve_market()
    print(result)