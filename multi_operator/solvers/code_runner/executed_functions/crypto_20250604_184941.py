import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_eth_price_data(start_time, end_time):
    """
    Fetches Ethereum price data from Binance using the proxy endpoint with a fallback to the primary endpoint.
    Args:
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    Returns:
        list: List of price data or None if both requests fail.
    """
    params = {
        "symbol": "ETHUSDT",
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        try:
            # Fallback to the primary endpoint
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Both proxy and primary endpoint failed: {e}")
            return None

def check_eth_price_threshold(start_date, end_date, threshold=8000):
    """
    Checks if the Ethereum price reached a specified threshold at any point between two dates.
    Args:
        start_date (datetime): Start date.
        end_date (datetime): End date.
        threshold (float): Price threshold to check.
    Returns:
        str: 'p1' if the price never reached the threshold, 'p2' if it did.
    """
    # Convert dates to UTC timestamps in milliseconds
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)

    # Fetch price data
    data = fetch_eth_price_data(start_time, end_time)
    if data:
        for candle in data:
            high_price = float(candle[2])  # High price is at index 2
            if high_price >= threshold:
                return "p2"  # Price reached the threshold
        return "p1"  # Price did not reach the threshold
    else:
        return "p3"  # Unknown due to data fetch failure

def main():
    # Define the time period for the query
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 5, 1))
    end_date = tz.localize(datetime(2025, 5, 31, 23, 59, 59))

    # Check if Ethereum reached the price threshold
    result = check_eth_price_threshold(start_date, end_date)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()