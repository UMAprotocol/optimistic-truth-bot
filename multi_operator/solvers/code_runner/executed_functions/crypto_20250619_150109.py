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

def get_eth_price_data(date_str, hour, minute, timezone_str):
    """
    Fetches the ETH/USDT price data for a specific hour candle on Binance.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format
        minute: Minute
        timezone_str: Timezone string

    Returns:
        Tuple of (open_price, close_price)
    """
    try:
        tz = pytz.timezone(timezone_str)
        dt = datetime.strptime(f"{date_str} {hour}:{minute}", "%Y-%m-%d %H:%M")
        dt_local = tz.localize(dt)
        dt_utc = dt_local.astimezone(pytz.utc)

        # Convert to milliseconds since this is what Binance API expects
        start_time = int(dt_utc.timestamp() * 1000)
        end_time = start_time + 3600000  # 1 hour later

        # URLs for API requests
        proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
        primary_url = "https://api.binance.com/api/v3/klines"

        # Parameters for the API request
        params = {
            "symbol": "ETHUSDT",
            "interval": "1h",
            "startTime": start_time,
            "endTime": end_time,
            "limit": 1
        }

        # First try the proxy endpoint
        response = requests.get(proxy_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                open_price = float(data[0][1])
                close_price = float(data[0][4])
                return (open_price, close_price)
            else:
                raise ValueError("No data returned from proxy endpoint.")
        else:
            raise ConnectionError("Failed to fetch data from proxy endpoint.")

    except Exception as e:
        logger.error(f"Proxy failed with error: {e}, trying primary endpoint.")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(primary_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return (open_price, close_price)
        else:
            raise ValueError("No data returned from primary endpoint.")

def main():
    """
    Main function to determine if the ETH price went up or down.
    """
    try:
        open_price, close_price = get_eth_price_data("2025-06-19", 10, 0, "US/Eastern")
        if close_price >= open_price:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logger.error(f"Error fetching price data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    main()