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

def get_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    try:
        # Try proxy endpoint first
        response = requests.get(
            proxy_url,
            params={"symbol": symbol, "interval": interval, "limit": 1, "startTime": start_time, "endTime": end_time},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")

        # Fallback to primary endpoint
        response = requests.get(
            primary_url,
            params={"symbol": symbol, "interval": interval, "limit": 1, "startTime": start_time, "endTime": end_time},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        logger.info("Data fetched successfully from primary endpoint.")
        return data

def resolve_market(symbol, target_date):
    """
    Resolves the market based on the price change of the specified symbol at the given target date.
    """
    # Convert target date to UTC timestamp for the start and end of the hour
    tz = pytz.timezone("US/Eastern")
    dt = datetime.strptime(target_date, "%Y-%m-%d %H:%M")
    dt_start = tz.localize(dt)
    dt_end = tz.localize(dt + timedelta(minutes=59, seconds=59))

    start_time = int(dt_start.timestamp() * 1000)
    end_time = int(dt_end.timestamp() * 1000)

    # Fetch data from Binance
    data = get_binance_data(symbol, "1h", start_time, end_time)

    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = (close_price - open_price) / open_price

        if price_change >= 0:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    """
    Main function to handle the resolution of the market.
    """
    symbol = "BTCUSDT"
    target_date = "2025-05-29 02:00"
    result = resolve_market(symbol, target_date)
    print(result)

if __name__ == "__main__":
    main()