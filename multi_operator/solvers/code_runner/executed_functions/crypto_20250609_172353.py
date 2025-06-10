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
        float: The lowest price within the given time frame or None if not found.
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
        print(f"Proxy failed, error: {e}, trying primary API")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(f"{PRIMARY_API_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Both proxy and primary API requests failed: {e}")
            return None

    # Find the lowest price in the returned data
    lowest_price = None
    for candle in data:
        low_price = float(candle[3])  # Low price is the fourth element in the list
        if lowest_price is None or low_price < lowest_price:
            lowest_price = low_price

    return lowest_price

def check_price_dip_to_threshold(symbol, start_date, end_date, threshold_price):
    """
    Checks if the price of a symbol dips to or below a threshold between two dates.
    
    Args:
        symbol (str): The trading symbol.
        start_date (datetime): Start date.
        end_date (datetime): End date.
        threshold_price (float): Price threshold to check.
    
    Returns:
        str: 'p1' if the price never dips to or below the threshold, 'p2' if it does.
    """
    # Convert dates to milliseconds since the epoch
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)

    lowest_price = fetch_price_data(symbol, start_time, end_time)

    if lowest_price is not None and lowest_price <= threshold_price:
        return "p2"  # Yes, price dipped to or below the threshold
    else:
        return "p1"  # No, price did not dip to or below the threshold

def main():
    # Define the parameters for the query
    symbol = "HYPEUSDC"
    start_date = datetime(2025, 5, 7, 16, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone("US/Eastern"))
    threshold_price = 10.0

    # Perform the check
    result = check_price_dip_to_threshold(symbol, start_date, end_date, threshold_price)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()