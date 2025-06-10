import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Define the API endpoints
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

def check_price_dip_to_nine(symbol, start_date, end_date):
    """
    Checks if the price of a symbol dipped to $9.000 or lower between two dates.
    
    Args:
        symbol (str): The trading pair symbol.
        start_date (datetime): Start date.
        end_date (datetime): End date.
    
    Returns:
        str: 'p1' if no dip to $9.000 or lower, 'p2' if there was a dip, 'p4' if data is unavailable.
    """
    # Convert dates to milliseconds since epoch
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)
    
    # Fetch price data
    data = fetch_price_data(symbol, start_time, end_time)
    
    if data:
        # Check if any low prices in the data dipped to $9.000 or lower
        for candle in data:
            low_price = float(candle[3])  # Low price is the fourth element in the list
            if low_price <= 9.000:
                return "p2"  # Yes, there was a dip
        return "p1"  # No dip found
    else:
        return "p4"  # Data unavailable

def main():
    # Define the symbol and the date range for the query
    symbol = "HYPE/USDC"
    start_date = datetime(2025, 5, 7, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone("US/Eastern"))
    
    # Check for price dip to $9.000 or lower
    result = check_price_dip_to_nine(symbol, start_date, end_date)
    
    # Print the result
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()