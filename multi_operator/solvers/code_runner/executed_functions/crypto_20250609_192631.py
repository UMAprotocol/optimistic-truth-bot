import requests
import logging
from datetime import datetime
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
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
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
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
        else:
            raise ValueError("No data returned from proxy endpoint.")
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to primary endpoint
        try:
            response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Primary endpoint also failed: {e}")
            raise

def get_close_price(symbol, date_str, timezone_str="US/Eastern"):
    """
    Get the closing price of a symbol at a specific date and time from Binance.
    """
    # Convert date string to the correct timestamp
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    start_time = int(utc_datetime.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 60000  # One minute later

    data = fetch_binance_data(symbol, "1m", start_time, end_time)
    if data and len(data) > 0:
        close_price = float(data[0][4])  # Close price is the 5th element
        return close_price
    else:
        raise ValueError("No data available for the specified time and symbol.")

def main():
    """
    Main function to determine if BTC closed below $98K on May 16, 2025.
    """
    try:
        close_price = get_close_price("BTCUSDT", "2025-05-16 12:00", "US/Eastern")
        logger.info(f"Close price for BTC on May 16, 2025 at 12:00 ET: {close_price}")
        if close_price <= 97999.99:
            print("recommendation: p2")  # Yes, it closed below $98K
        else:
            print("recommendation: p1")  # No, it did not close below $98K
    except Exception as e:
        logger.error(f"Failed to fetch or process data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()