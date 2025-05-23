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
PRIMARY_API_URL = "https://api.binance.com/api/v3"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    
    Args:
        symbol (str): The symbol to fetch data for.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        float: The highest price found in the data.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Max limit
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(f"{PROXY_API_URL}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary API.")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(f"{PRIMARY_API_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

    # Extract the highest price from the data
    highest_price = max(float(candle[2]) for candle in data) if data else None
    return highest_price

def check_price_threshold(symbol, start_date, end_date, threshold_price):
    """
    Checks if the price of a symbol has reached a threshold between two dates.
    
    Args:
        symbol (str): The symbol to check.
        start_date (datetime): Start date.
        end_date (datetime): End date.
        threshold_price (float): Price threshold to check.
    
    Returns:
        str: 'p1' if the price never reached the threshold, 'p2' if it did.
    """
    # Convert dates to milliseconds since the epoch
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)

    highest_price = fetch_price_data(symbol, start_time, end_time)

    if highest_price is None:
        return "p3"  # Unknown or API failure
    elif highest_price >= threshold_price:
        return "p2"  # Yes, price reached the threshold
    else:
        return "p1"  # No, price did not reach the threshold

def main():
    # Define the symbol and the threshold price
    symbol = "HYPEUSDC"
    threshold_price = 35.0

    # Define the time period (Eastern Time)
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 5, 7, 16, 0, 0))
    end_date = tz.localize(datetime(2025, 5, 31, 23, 59, 59))

    # Check if the price threshold was reached
    result = check_price_threshold(symbol, start_date, end_date, threshold_price)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()