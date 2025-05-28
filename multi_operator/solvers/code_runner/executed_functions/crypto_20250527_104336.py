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

def get_btc_price_at_time(target_time_utc):
    """
    Fetches the BTC price at a specific UTC time using Binance API.
    
    Args:
        target_time_utc (datetime): The target UTC datetime to fetch the price for.
    
    Returns:
        float: The BTC price at the specified time.
    """
    symbol = "BTCUSDT"
    interval = "1m"
    limit = 1
    start_time = int(target_time_utc.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later in milliseconds

    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params={
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
            "startTime": start_time,
            "endTime": end_time
        }, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")

        # Fallback to primary endpoint
        try:
            response = requests.get(primary_url, params={
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
                "startTime": start_time,
                "endTime": end_time
            }, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return float(data[0][4])  # Close price
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}")
            raise

def main():
    # Target time in Beijing time
    beijing_time = datetime(2025, 5, 27, 23, 0, 0)
    beijing_tz = pytz.timezone("Asia/Shanghai")
    target_time_local = beijing_tz.localize(beijing_time)
    target_time_utc = target_time_local.astimezone(pytz.utc)

    try:
        btc_price = get_btc_price_at_time(target_time_utc)
        logger.info(f"BTC price at {target_time_utc} UTC is {btc_price}")
        if btc_price > 150000:
            print("recommendation: p1")
        else:
            print("recommendation: p2")
    except Exception as e:
        logger.error(f"Failed to fetch BTC price: {e}")
        print("recommendation: p4")

if __name__ == "__main__":
    main()