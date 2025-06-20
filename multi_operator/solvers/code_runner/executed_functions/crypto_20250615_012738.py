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

def fetch_price_data(symbol, interval, start_time, end_time, proxy_url, primary_url):
    """
    Fetches price data from Binance using a proxy and falls back to the primary endpoint if necessary.
    """
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
        data = response.json()
        logger.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logger.error(f"Failed to fetch data from proxy endpoint: {e}. Trying primary endpoint.")
        # Fallback to the primary endpoint
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Failed to fetch data from both endpoints: {e}")
            raise

def get_eth_price_change(date_str, hour, minute, timezone_str):
    """
    Determines the percentage change in ETH price for a specific 1-hour candle on Binance.
    """
    # Convert local time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    local_time = tz.localize(datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S"))
    utc_time = local_time.astimezone(pytz.utc)
    start_time = int(utc_time.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # API endpoints
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    # Fetch price data
    data = fetch_price_data("ETHUSDT", "1h", start_time, end_time, proxy_url, primary_url)

    # Calculate percentage change
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        change_percent = ((close_price - open_price) / open_price) * 100
        return change_percent
    else:
        logger.error("No data available for the specified time.")
        return None

def main():
    """
    Main function to determine if the ETH price went up or down.
    """
    try:
        change = get_eth_price_change("2025-06-14", 20, 0, "US/Eastern")
        if change is not None:
            if change >= 0:
                print("recommendation: p2")  # Up
            else:
                print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # Unknown/50-50
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()