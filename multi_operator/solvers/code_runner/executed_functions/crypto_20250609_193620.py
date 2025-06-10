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
PRIMARY_API_ENDPOINT = "https://api.binance.com/api/v3/klines"
PROXY_API_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API for a given symbol within a specified time range.
    Implements a fallback mechanism from proxy to primary endpoint.
    
    Args:
        symbol (str): The symbol to fetch data for, e.g., 'SUIUSDT'.
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.
    
    Returns:
        list: List of price data or None if both requests fail.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum number of data points
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")

    try:
        # Fallback to the primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Primary endpoint also failed: {e}")

    return None

def check_price_dip_to_target(symbol, start_date, end_date, target_price):
    """
    Checks if the price of a symbol dipped to or below a target price between two dates.
    
    Args:
        symbol (str): The trading symbol, e.g., 'SUIUSDT'.
        start_date (datetime): Start date.
        end_date (datetime): End date.
        target_price (float): Target price to check.
    
    Returns:
        bool: True if price dipped to or below the target, False otherwise.
    """
    # Convert dates to milliseconds since epoch
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)

    # Fetch price data
    price_data = fetch_price_data(symbol, start_time, end_time)

    if price_data:
        # Check if any 'Low' price in the data is less than or equal to the target price
        for candle in price_data:
            low_price = float(candle[3])  # 'Low' price is at index 3
            if low_price <= target_price:
                return True
    return False

def main():
    # Define the symbol and target price
    symbol = "SUIUSDT"
    target_price = 1.9

    # Define the time range (May 7, 2025 to May 31, 2025 in ET timezone)
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 5, 7))
    end_date = tz.localize(datetime(2025, 5, 31, 23, 59))

    # Check if the price dipped to the target
    price_dipped = check_price_dip_to_target(symbol, start_date, end_date, target_price)

    # Print the result based on the price check
    if price_dipped:
        print("recommendation: p2")  # Yes, price dipped to $1.9 or lower
    else:
        print("recommendation: p1")  # No, price did not dip to $1.9 or lower

if __name__ == "__main__":
    main()