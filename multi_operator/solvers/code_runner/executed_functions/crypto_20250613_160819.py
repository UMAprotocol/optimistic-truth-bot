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

def get_data(symbol, start_time, end_time, proxy_url, primary_url):
    """
    Fetches data from Binance API using a proxy and falls back to the primary endpoint if necessary.
    """
    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Close price
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}/klines?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Close price

def convert_to_utc_timestamp(date_str, hour, minute, timezone_str):
    """
    Converts local time to UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(timezone_str)
    local_time = tz.localize(datetime.strptime(f"{date_str} {hour:02d}:{minute:02d}", "%Y-%m-%d %H:%M"))
    utc_time = local_time.astimezone(pytz.utc)
    return int(utc_time.timestamp() * 1000)

def main():
    """
    Main function to fetch and compare Solana prices on Binance.
    """
    symbol = "SOLUSDT"
    timezone_str = "US/Eastern"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3"

    # Convert dates and times to UTC timestamps
    start_time_12_jun = convert_to_utc_timestamp("2025-06-12", 12, 0, timezone_str)
    end_time_12_jun = start_time_12_jun + 60000  # 1 minute later

    start_time_13_jun = convert_to_utc_timestamp("2025-06-13", 12, 0, timezone_str)
    end_time_13_jun = start_time_13_jun + 60000  # 1 minute later

    # Fetch close prices
    close_price_12_jun = get_data(symbol, start_time_12_jun, end_time_12_jun, proxy_url, primary_url)
    close_price_13_jun = get_data(symbol, start_time_13_jun, end_time_13_jun, proxy_url, primary_url)

    # Determine resolution
    if close_price_12_jun < close_price_13_jun:
        recommendation = "p2"  # Up
    elif close_price_12_jun > close_price_13_jun:
        recommendation = "p1"  # Down
    else:
        recommendation = "p3"  # 50-50

    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()