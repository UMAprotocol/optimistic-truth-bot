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

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")

        # Fallback to the primary endpoint
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}")
            raise

def get_price_change(symbol, target_time):
    """
    Determines the price change for a given symbol at a specific time.
    """
    # Convert target time to UTC milliseconds
    target_time_utc = target_time.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later

    # Fetch data from Binance
    data = fetch_binance_data(symbol, "1h", start_time_ms, end_time_ms)

    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change_percent = ((close_price - open_price) / open_price) * 100
        return price_change_percent
    else:
        raise ValueError("No data available for the specified time and symbol.")

def main():
    """
    Main function to determine if the Bitcoin price went up or down on June 11, 12AM ET.
    """
    symbol = "BTCUSDT"
    target_time_str = "2025-06-11 00:00:00"
    timezone_str = "US/Eastern"

    # Parse the target time
    target_time = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
    target_time = pytz.timezone(timezone_str).localize(target_time)

    try:
        price_change_percent = get_price_change(symbol, target_time)
        logger.info(f"Price change percentage: {price_change_percent}%")

        if price_change_percent >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logger.error(f"Error determining price change: {e}")
        print("recommendation: p3")  # Unknown/50-50

if __name__ == "__main__":
    main()