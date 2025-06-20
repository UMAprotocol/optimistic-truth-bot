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
        json: The response from the API.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum allowed by Binance for one request
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def check_xrp_price_threshold(start_date, end_date, threshold):
    """
    Checks if the XRP price has reached a certain threshold within a given date range.
    
    Args:
        start_date (datetime): Start date in ET timezone.
        end_date (datetime): End date in ET timezone.
        threshold (float): Price threshold to check.
    
    Returns:
        str: 'p1' if the price never reached the threshold, 'p2' if it did.
    """
    # Convert datetime to UTC and then to milliseconds
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)
    
    # Fetch data
    data = fetch_data_from_binance("XRPUSDT", start_time, end_time)
    
    # Check if any high price in the data exceeds the threshold
    for candle in data:
        high_price = float(candle[2])  # High price is the third element in each candle
        if high_price >= threshold:
            return "p2"  # Yes, price reached the threshold
    
    return "p1"  # No, price never reached the threshold

def main():
    # Define the date range in ET timezone
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 6, 1, 0, 0, 0))
    end_date = tz.localize(datetime(2025, 6, 30, 23, 59, 59))
    
    # Price threshold to check
    threshold = 2.3
    
    # Check if XRP reached the threshold in June 2025
    result = check_xrp_price_threshold(start_date, end_date, threshold)
    
    # Print the result
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()