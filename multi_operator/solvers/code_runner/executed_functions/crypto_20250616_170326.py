import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_eth_price_change(date_str, hour=12, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the percentage change for the ETH/USDT pair from Binance for a specific hour candle.

    Args:
        date_str (str): Date in YYYY-MM-DD format.
        hour (int): Hour the candle starts.
        minute (int): Minute the candle starts.
        timezone_str (str): Timezone string.

    Returns:
        float: Percentage change of the ETH/USDT price.
    """
    # Convert local time to UTC
    tz = pytz.timezone(timezone_str)
    naive_dt = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
    local_dt = tz.localize(naive_dt)
    utc_dt = local_dt.astimezone(pytz.utc)

    # Calculate timestamps in milliseconds
    start_timestamp = int(utc_dt.timestamp() * 1000)
    end_timestamp = start_timestamp + 3600000  # 1 hour later

    # Construct the URL for the proxy API
    proxy_url = f"{PROXY_BINANCE_API}?symbol=ETHUSDT&interval=1h&limit=1&startTime={start_timestamp}&endTime={end_timestamp}"

    # Construct the URL for the primary API
    primary_url = f"{PRIMARY_BINANCE_API}/klines?symbol=ETHUSDT&interval=1h&limit=1&startTime={start_timestamp}&endTime={end_timestamp}"

    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(proxy_url)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy endpoint.")
    except Exception as e:
        logging.error(f"Failed to fetch data from proxy endpoint: {e}. Trying primary endpoint.")
        # Fallback to the primary endpoint
        response = requests.get(primary_url)
        response.raise_for_status()
        data = response.json()

    # Calculate the percentage change
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        percent_change = ((close_price - open_price) / open_price) * 100
        return percent_change
    else:
        raise ValueError("No data available for the specified time and date.")

def main():
    # Example date and time for the query
    date_str = "2025-06-16"
    hour = 12
    minute = 0
    timezone_str = "US/Eastern"

    try:
        percent_change = fetch_eth_price_change(date_str, hour, minute, timezone_str)
        if percent_change >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50

if __name__ == "__main__":
    main()