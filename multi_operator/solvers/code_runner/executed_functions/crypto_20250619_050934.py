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

def get_eth_price_data(date_str, hour=0, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the open and close price for the ETH/USDT 1 Hour candle on Binance at a specific time.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format (default: 0)
        minute: Minute (default: 0)
        timezone_str: Timezone string (default: "US/Eastern")

    Returns:
        Tuple of (open_price, close_price)
    """
    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    target_time_local = tz.localize(datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(pytz.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)

    # Binance API endpoints
    primary_url = "https://api.binance.com/api/v3/klines"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

    params = {
        "symbol": "ETHUSDT",
        "interval": "1h",
        "limit": 1,
        "startTime": start_time_ms,
        "endTime": start_time_ms + 3600000  # 1 hour later
    }

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return (open_price, close_price)
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")

        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                open_price = float(data[0][1])
                close_price = float(data[0][4])
                return (open_price, close_price)
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}")
            raise

def main():
    """
    Main function to determine if the ETH price went up or down on June 19, 2025 at 12AM ET.
    """
    try:
        open_price, close_price = get_eth_price_data("2025-06-19", 0, 0, "US/Eastern")
        if close_price >= open_price:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logger.error(f"Failed to fetch price data: {e}")
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()