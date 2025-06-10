import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API configuration
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API using a proxy and falls back to the primary endpoint if necessary.
    
    Args:
        symbol (str): The trading pair symbol.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        float: The lowest price within the given time frame or None if no data is available.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum number of candles to fetch
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            # Extract the lowest price from the candle data
            return min(float(candle[3]) for candle in data)  # Index 3 is the low price in candle data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return min(float(candle[3]) for candle in data)
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_price_dip(symbol, start_date, end_date, target_price):
    """
    Checks if the price of a symbol dipped to or below a target price between two dates.
    
    Args:
        symbol (str): The trading pair symbol.
        start_date (datetime): Start date.
        end_date (datetime): End date.
        target_price (float): Target price to check.
    
    Returns:
        str: 'p2' if price dipped to or below target price, otherwise 'p1'.
    """
    # Convert dates to milliseconds since epoch
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)
    
    # Fetch the lowest price in the given time frame
    lowest_price = fetch_price_data(symbol, start_time, end_time)
    
    if lowest_price is not None and lowest_price <= target_price:
        return "p2"  # Yes, price dipped to or below target price
    else:
        return "p1"  # No, price did not dip to or below target price

def main():
    # Define the parameters for the market question
    symbol = "HYPEUSDC"
    start_date = datetime(2025, 5, 7, 16, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone("US/Eastern"))
    target_price = 12.0
    
    # Check if the price dipped to or below the target price
    result = check_price_dip(symbol, start_date, end_date, target_price)
    
    # Print the recommendation based on the result
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()