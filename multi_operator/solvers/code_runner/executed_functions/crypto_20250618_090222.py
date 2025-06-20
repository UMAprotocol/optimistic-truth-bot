import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import pytz
import logging

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_price_data(symbol, interval, start_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }

    try:
        # Try fetching data from the proxy API first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logging.warning(f"Proxy API failed: {e}. Attempting primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logging.error(f"Primary API failed: {e}.")
            raise

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price data fetched for the specified symbol and time.
    """
    # Convert target time to UTC timestamp
    target_datetime = datetime.strptime(target_time, "%Y-%m-%d %H:%M %Z")
    target_timestamp = int(target_datetime.replace(tzinfo=timezone.utc).timestamp() * 1000)

    # Fetch price data
    data = fetch_price_data(symbol, "1h", target_timestamp)

    # Extract open and close prices
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])

        # Determine if the price went up or down
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    """
    Main function to handle the resolution of the market.
    """
    # Example: Solana price on June 18, 2025, 4 AM ET
    symbol = "SOLUSDT"
    target_time = "2025-06-18 04:00 ET"

    try:
        result = resolve_market(symbol, target_time)
        print(result)
    except Exception as e:
        logging.error(f"Error resolving market: {e}")
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()