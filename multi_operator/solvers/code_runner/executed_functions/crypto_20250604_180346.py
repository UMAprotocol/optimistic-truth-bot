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

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API for a given symbol within a specified time range.
    Args:
        symbol (str): The symbol to fetch data for (e.g., 'SOLUSDT').
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    Returns:
        list: List of price data or None if no data is found.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to the primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            return None

def check_solana_price_threshold(start_date, end_date, threshold=300.00):
    """
    Checks if the price of Solana ever reaches or exceeds a threshold within a given date range.
    Args:
        start_date (datetime): Start date.
        end_date (datetime): End date.
        threshold (float): Price threshold to check.
    Returns:
        str: 'p1' if the price never reaches the threshold, 'p2' if it does.
    """
    # Convert datetime to milliseconds since epoch
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)

    # Fetch price data
    price_data = fetch_price_data("SOLUSDT", start_time, end_time)

    if price_data:
        for candle in price_data:
            high_price = float(candle[2])  # High price is at index 2
            if high_price >= threshold:
                return "p2"  # Yes, price reached or exceeded the threshold
    return "p1"  # No, price never reached the threshold

def main():
    # Define the date range for May 2025 in Eastern Time
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 5, 1, 0, 0, 0))
    end_date = tz.localize(datetime(2025, 5, 31, 23, 59, 59))

    # Check if Solana reaches $300 in May 2025
    result = check_solana_price_threshold(start_date, end_date)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()