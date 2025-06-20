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

def fetch_eth_price(date_str, hour, minute, timezone_str):
    """
    Fetches the closing price of the ETH/USDT pair from Binance for a specific hour candle.

    Args:
        date_str (str): Date in YYYY-MM-DD format.
        hour (int): Hour of the day (24-hour format).
        minute (int): Minute of the hour.
        timezone_str (str): Timezone string.

    Returns:
        float: The closing price of the ETH/USDT pair.
    """
    # Convert local time to UTC
    tz = pytz.timezone(timezone_str)
    local_dt = tz.localize(datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S"))
    utc_dt = local_dt.astimezone(pytz.utc)

    # Calculate timestamps for the start and end of the hour
    start_timestamp = int(utc_dt.timestamp() * 1000)  # Convert to milliseconds
    end_timestamp = int((utc_dt + timedelta(minutes=59, seconds=59)).timestamp() * 1000)

    # URLs for Binance API
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    # Try fetching data from the proxy endpoint first
    try:
        response = requests.get(
            proxy_url,
            params={
                "symbol": "ETHUSDT",
                "interval": "1h",
                "limit": 1,
                "startTime": start_timestamp,
                "endTime": end_timestamp
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Closing price
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")

    # Fallback to the primary endpoint if proxy fails
    try:
        response = requests.get(
            primary_url,
            params={
                "symbol": "ETHUSDT",
                "interval": "1h",
                "limit": 1,
                "startTime": start_timestamp,
                "endTime": end_timestamp
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Closing price
    except Exception as e:
        logger.error(f"Primary endpoint failed: {e}")
        raise

def main():
    """
    Main function to determine if the price of ETH/USDT went up or down.
    """
    # Specific date and time for the query
    date_str = "2025-06-12"
    hour = 11
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
        logger.error(f"Error fetching price data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    main()