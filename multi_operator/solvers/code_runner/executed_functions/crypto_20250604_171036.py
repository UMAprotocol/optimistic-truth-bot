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
    Fetches price data from Binance API with a fallback to a proxy server.
    
    Args:
        symbol (str): The symbol to fetch data for.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        float: The lowest price in the given time frame or None if no data could be fetched.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Max limit to ensure coverage of the period
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try fetching from the proxy first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            # Extract the lowest price from the 'L' (low) price in each candle
            return min(float(candle[3]) for candle in data)
    except Exception as e:
        print(f"Proxy failed with error: {e}, falling back to primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return min(float(candle[3]) for candle in data)
        except Exception as e:
            print(f"Primary API also failed with error: {e}")

    return None

def check_price_dip(symbol, start_date, end_date, threshold_price):
    """
    Checks if the price of a symbol dipped below a certain threshold between two dates.
    
    Args:
        symbol (str): The trading symbol.
        start_date (datetime): Start date.
        end_date (datetime): End date.
        threshold_price (float): Price threshold to check.
    
    Returns:
        str: 'p2' if price dipped below threshold, 'p1' otherwise.
    """
    # Convert dates to milliseconds since epoch
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)

    lowest_price = fetch_price_data(symbol, start_time, end_time)
    if lowest_price is not None and lowest_price <= threshold_price:
        return "p2"  # Yes, price dipped below threshold
    else:
        return "p1"  # No, price did not dip below threshold

def main():
    # Define the symbol and threshold price
    symbol = "HYPEUSDC"
    threshold_price = 9.0

    # Define the time period (Eastern Time)
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 5, 7, 16, 0, 0))
    end_date = tz.localize(datetime(2025, 5, 31, 23, 59, 59))

    # Check if the price dipped below the threshold
    result = check_price_dip(symbol, start_date, end_date, threshold_price)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()