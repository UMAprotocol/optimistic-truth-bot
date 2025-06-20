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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def fetch_eth_price(date_str, hour, minute, timezone_str):
    """
    Fetches the closing price of the ETH/USDT pair from Binance for a specific hour candle.
    """
    # Convert local time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {hour}:{minute}", "%Y-%m-%d %H:%M")
    local_time = tz.localize(local_time)
    utc_time = local_time.astimezone(pytz.utc)
    start_time = int(utc_time.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # URLs setup
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    # Try fetching data from the proxy endpoint
    try:
        response = requests.get(
            proxy_url,
            params={
                "symbol": "ETHUSDT",
                "interval": "1h",
                "limit": 1,
                "startTime": start_time,
                "endTime": end_time
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if data:
            close_price = float(data[0][4])
            return close_price
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")

    # Fallback to the primary endpoint
    try:
        response = requests.get(
            primary_url,
            params={
                "symbol": "ETHUSDT",
                "interval": "1h",
                "limit": 1,
                "startTime": start_time,
                "endTime": end_time
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if data:
            close_price = float(data[0][4])
            return close_price
    except Exception as e:
        logger.error(f"Primary endpoint also failed: {e}")
        raise

def main():
    """
    Main function to determine if the price of ETH/USDT went up or down at a specific time.
    """
    # Specific date and time for the query
    date_str = "2025-06-15"
    hour = 2  # 2 AM ET
    minute = 0
    timezone_str = "US/Eastern"

    try:
        initial_price = fetch_eth_price(date_str, hour, minute, timezone_str)
        final_price = fetch_eth_price(date_str, hour + 1, minute, timezone_str)

        if final_price >= initial_price:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logger.error(f"Failed to fetch prices: {e}")
        print("recommendation: p3")  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    main()