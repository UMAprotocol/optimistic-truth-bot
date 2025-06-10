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
        symbol (str): The symbol to fetch data for (e.g., 'SUIUSDT').
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
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_price_dip_to_threshold(symbol, start_date, end_date, threshold):
    """
    Checks if the price of a symbol dips to or below a certain threshold within a given date range.
    Args:
        symbol (str): The symbol to check (e.g., 'SUIUSDT').
        start_date (datetime): Start date.
        end_date (datetime): End date.
        threshold (float): Price threshold to check.
    Returns:
        str: 'p2' if price dips to or below the threshold, 'p1' otherwise.
    """
    # Convert dates to milliseconds since the epoch
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)

    # Fetch price data
    price_data = fetch_price_data(symbol, start_time, end_time)
    if price_data:
        for candle in price_data:
            low_price = float(candle[3])  # Low price is at index 3
            if low_price <= threshold:
                return "p2"  # Yes, price dipped to or below the threshold
    return "p1"  # No, price did not dip to or below the threshold

def main():
    # Define the symbol and threshold
    symbol = "SUIUSDT"
    threshold = 2.0

    # Define the date range (Eastern Time)
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 5, 7))
    end_date = tz.localize(datetime(2025, 5, 31, 23, 59))

    # Check if the price dips to or below the threshold
    result = check_price_dip_to_threshold(symbol, start_date, end_date, threshold)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()