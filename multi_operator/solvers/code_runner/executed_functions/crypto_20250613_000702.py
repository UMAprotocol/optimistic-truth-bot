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
        # Try fetching data using the proxy endpoint
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logger.error(f"Failed to fetch data from proxy: {e}. Trying primary endpoint.")
        try:
            # Fallback to the primary endpoint if proxy fails
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logger.error(f"Failed to fetch data from primary endpoint: {e}")
            raise

def get_eth_price_change(date_str, hour):
    """
    Determines if the ETH price went up or down at the specified hour on the given date.
    """
    tz = pytz.timezone("US/Eastern")
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    dt = tz.localize(datetime(dt.year, dt.month, dt.day, hour, 0, 0))
    start_time = int(dt.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    data = fetch_binance_data("ETHUSDT", "1h", start_time, end_time)
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50

def main():
    """
    Main function to determine if Ethereum's price went up or down.
    """
    try:
        result = get_eth_price_change("2025-06-12", 19)  # June 12, 2025, 7 PM ET
        print(f"recommendation: {result}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Default to unknown if there's an error

if __name__ == "__main__":
    main()