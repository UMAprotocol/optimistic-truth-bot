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

def fetch_data_from_binance(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    
    Args:
        symbol (str): The symbol to fetch data for.
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    
    Returns:
        list: Data from the API.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum limit
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
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            raise

def check_doge_price_threshold(start_date, end_date, threshold=0.50):
    """
    Checks if the Dogecoin price reached a certain threshold between two dates.
    
    Args:
        start_date (datetime): Start date.
        end_date (datetime): End date.
        threshold (float): Price threshold to check.
    
    Returns:
        str: 'p1' if the price never reached the threshold, 'p2' if it did.
    """
    # Convert dates to milliseconds since the epoch
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)
    
    # Fetch data
    data = fetch_data_from_binance("DOGEUSDT", start_time, end_time)
    
    # Check if any high price in the data reached the threshold
    for candle in data:
        high_price = float(candle[2])  # High price is the third element in each candle
        if high_price >= threshold:
            return "p2"  # Yes, price reached or exceeded the threshold
    
    return "p1"  # No, price never reached the threshold

def main():
    # Define the time period to check
    start_date = datetime(2025, 5, 1, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone("US/Eastern"))
    
    # Check if Dogecoin reached $0.50 in May 2025
    result = check_doge_price_threshold(start_date, end_date)
    
    # Print the result
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()