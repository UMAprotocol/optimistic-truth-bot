import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

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
        float: The highest price found in the given time range.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint first
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
    highest_price = 0
    for candle in data:
        high_price = float(candle[2])  # High price is at index 2
        if high_price > highest_price:
            highest_price = high_price
    
    return highest_price

def check_price_threshold(symbol, start_date, end_date, threshold):
    """
    Checks if the price of a symbol has reached a certain threshold between two dates.
    
    Args:
        symbol (str): The trading symbol.
        start_date (datetime): Start date.
        end_date (datetime): End date.
        threshold (float): Price threshold to check.
    
    Returns:
        str: 'p1' if the price never reached the threshold, 'p2' if it did.
    """
    # Convert dates to UTC timestamps in milliseconds
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)
    
    highest_price = fetch_price_data(symbol, start_timestamp, end_timestamp)
    
    if highest_price is None:
        return "p3"  # Unknown or API failure
    elif highest_price >= threshold:
        return "p2"  # Yes, price reached the threshold
    else:
        return "p1"  # No, price did not reach the threshold

def main():
    # Define the parameters for the query
    symbol = "HOUSE/SOL"
    threshold_price = 0.250
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone("US/Eastern"))
    
    # Check if the price threshold was reached
    result = check_price_threshold(symbol, start_date, end_date, threshold_price)
    
    # Print the result
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()