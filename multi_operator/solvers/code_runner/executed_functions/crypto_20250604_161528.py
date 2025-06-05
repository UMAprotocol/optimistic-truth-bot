import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API endpoints
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
        list: List of price data or None if both requests fail.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum allowed by Binance for one request
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data using the proxy URL
        response = requests.get(PROXY_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_price_dip_to_threshold(symbol, start_date, end_date, threshold_price):
    """
    Checks if the price of a symbol dipped to or below a threshold between two dates.
    
    Args:
        symbol (str): The trading pair symbol.
        start_date (datetime): Start date.
        end_date (datetime): End date.
        threshold_price (float): Price threshold to check.
    
    Returns:
        str: 'p1' if the price never dipped to or below the threshold, 'p2' if it did.
    """
    # Convert dates to milliseconds since epoch
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)
    
    # Fetch price data
    price_data = fetch_price_data(symbol, start_time, end_time)
    
    if price_data:
        # Check if any closing price in the data is less than or equal to the threshold
        for candle in price_data:
            close_price = float(candle[4])  # Closing price is the fifth element in each candle
            if close_price <= threshold_price:
                return "p2"  # Yes, price dipped to or below the threshold
        return "p1"  # No, price did not dip to or below the threshold
    else:
        return "p3"  # Unknown or data fetch error

def main():
    # Define the symbol and threshold price
    symbol = "HYPEUSDC"
    threshold_price = 16.0
    
    # Define the time period (Eastern Time)
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 5, 7, 16, 0, 0))
    end_date = tz.localize(datetime(2025, 5, 31, 23, 59, 59))
    
    # Check if the price dipped to the threshold
    result = check_price_dip_to_threshold(symbol, start_date, end_date, threshold_price)
    
    # Print the result
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()