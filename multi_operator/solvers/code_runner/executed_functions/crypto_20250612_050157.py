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
    Fetches price data from Binance using a proxy and falls back to the primary API if necessary.
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
    Calculates the percentage change in price for the ETH/USDT pair on Binance at a specific time.
    """
    tz = pytz.timezone(timezone_str)
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    dt = tz.localize(datetime(dt.year, dt.month, dt.day, hour, minute, 0))
    dt_utc = dt.astimezone(pytz.utc)
    start_time = int(dt_utc.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    data = fetch_price_data("ETHUSDT", "1h", start_time, end_time, proxy_url, primary_url)
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change_percentage = ((close_price - open_price) / open_price) * 100
        return price_change_percentage
    else:
        raise ValueError("No data available for the specified time and date.")

def main():
    """
    Main function to determine if the price of ETH/USDT was up or down at the specified time.
    """
    try:
        price_change = get_eth_price_change("2025-06-12", 0, 0, "US/Eastern")
        if price_change >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    main()