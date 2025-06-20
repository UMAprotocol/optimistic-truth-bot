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
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
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
        return response.json()
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to the primary endpoint
        response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def get_eth_price_change(date_str, hour, minute, timezone_str):
    """
    Calculates the percentage change for the ETH/USDT pair for a specific 1-hour candle.
    """
    tz = pytz.timezone(timezone_str)
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    dt = tz.localize(datetime(dt.year, dt.month, dt.day, hour, minute, 0))
    dt_utc = dt.astimezone(pytz.utc)
    start_time = int(dt_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour in milliseconds

    data = fetch_binance_data("ETHUSDT", "1h", start_time, end_time)
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        change_percent = ((close_price - open_price) / open_price) * 100
        return change_percent
    else:
        raise ValueError("No data returned from Binance for the specified time.")

def main():
    """
    Main function to determine if the ETH price went up or down at a specific time.
    """
    try:
        change_percent = get_eth_price_change("2025-06-17", 15, 0, "US/Eastern")
        if change_percent >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 if error occurs

if __name__ == "__main__":
    main()