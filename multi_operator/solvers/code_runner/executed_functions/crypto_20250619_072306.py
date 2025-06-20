import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_eth_price_from_binance(start_time, end_time):
    """
    Fetches Ethereum prices from Binance within a specified time range.
    Args:
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    Returns:
        list: List of prices or None if no data could be fetched.
    """
    params = {
        "symbol": "ETHUSDT",
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return [float(candle[4]) for candle in data]  # Extract closing prices
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to the primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return [float(candle[4]) for candle in data]  # Extract closing prices
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_eth_price_exceeds_threshold(prices, threshold):
    """
    Checks if any of the Ethereum prices exceeds the given threshold.
    Args:
        prices (list): List of Ethereum prices.
        threshold (float): Price threshold to check against.
    Returns:
        bool: True if any price exceeds the threshold, False otherwise.
    """
    return any(price > threshold for price in prices)

def main():
    # Define the observation window in London time (UTC+1)
    london_tz = pytz.timezone("Europe/London")
    start_date = london_tz.localize(datetime(2025, 6, 18, 0, 0, 0))
    end_date = london_tz.localize(datetime(2025, 6, 18, 23, 59, 59))

    # Convert to UTC timestamps in milliseconds
    start_time_utc_ms = int(start_date.astimezone(pytz.utc).timestamp() * 1000)
    end_time_utc_ms = int(end_date.astimezone(pytz.utc).timestamp() * 1000)

    # Fetch Ethereum prices from Binance
    prices = fetch_eth_price_from_binance(start_time_utc_ms, end_time_utc_ms)

    if prices is None:
        print("recommendation: p4")  # Unable to fetch data
    elif check_eth_price_exceeds_threshold(prices, 2750):
        print("recommendation: p2")  # Yes, price exceeded $2750
    else:
        print("recommendation: p1")  # No, price did not exceed $2750

if __name__ == "__main__":
    main()