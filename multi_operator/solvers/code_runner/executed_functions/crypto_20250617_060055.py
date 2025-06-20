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

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching from proxy first
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logger.error(f"Proxy failed with error: {e}. Trying primary endpoint.")
        try:
            # Fallback to primary endpoint
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Primary endpoint failed with error: {e}.")
            raise

def get_eth_price_change():
    """
    Determines if the ETH price went up or down based on the 1-hour candle starting at 1 AM ET on June 17, 2025.
    """
    # Convert 1 AM ET on June 17, 2025 to UTC timestamp
    et_timezone = pytz.timezone("US/Eastern")
    target_time = et_timezone.localize(datetime(2025, 6, 17, 1, 0, 0))
    target_time_utc = target_time.astimezone(pytz.utc)
    start_time = int(target_time_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    try:
        data = fetch_binance_data("ETHUSDT", "1h", start_time, end_time)
        if data and len(data) > 0:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            price_change = close_price - open_price
            if price_change >= 0:
                return "p2"  # Up
            else:
                return "p1"  # Down
        else:
            logger.error("No data available for the specified time.")
            return "p3"  # Unknown/50-50
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return "p3"  # Unknown/50-50

def main():
    """
    Main function to determine if ETH price went up or down.
    """
    result = get_eth_price_change()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()