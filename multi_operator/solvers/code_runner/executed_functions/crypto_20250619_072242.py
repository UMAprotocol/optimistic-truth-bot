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
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_eth_price_from_binance(start_time, end_time):
    """
    Fetches Ethereum prices from Binance within a specified time range.
    Args:
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.
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
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return [float(candle[4]) for candle in data]  # Extract closing prices
    except Exception as e:
        print(f"Proxy failed, error: {e}, trying primary endpoint.")
        try:
            # Fallback to the primary endpoint if proxy fails
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return [float(candle[4]) for candle in data]  # Extract closing prices
        except Exception as e:
            print(f"Both proxy and primary endpoints failed, error: {e}")
            return None

def check_eth_price_exceeds_threshold(start_date, end_date, threshold):
    """
    Checks if the Ethereum price exceeds a certain threshold within a given date range.
    Args:
        start_date (datetime): Start date and time.
        end_date (datetime): End date and time.
        threshold (float): Price threshold to check.
    Returns:
        bool: True if price exceeds threshold, False otherwise.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)
    
    prices = fetch_eth_price_from_binance(start_time, end_time)
    if prices:
        return any(price > threshold for price in prices)
    return False

def main():
    # Define the time range for the query
    london_tz = pytz.timezone("Europe/London")
    start_date = london_tz.localize(datetime(2025, 6, 18, 0, 0, 0))
    end_date = london_tz.localize(datetime(2025, 6, 18, 23, 59, 59))
    threshold = 2750.0
    
    # Check if the price of Ethereum exceeds the threshold
    result = check_eth_price_exceeds_threshold(start_date, end_date, threshold)
    
    # Print the result based on the check
    if result:
        print("recommendation: p2")  # Yes, price exceeds threshold
    else:
        print("recommendation: p1")  # No, price does not exceed threshold

if __name__ == "__main__":
    main()