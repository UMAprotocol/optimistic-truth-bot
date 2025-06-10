import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys are not required for this specific task as we are accessing public endpoints
# However, if needed, they can be loaded like this:
# BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

def fetch_fartcoin_price_data(start_time, end_time):
    """
    Fetches Fartcoin price data from Dexscreener proxy and primary endpoints.
    
    Args:
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.
    
    Returns:
        list: List of price data or None if both requests fail.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3"
    params = {
        "symbol": "FARTCOINSOL",
        "interval": "1m",
        "limit": 1000,  # Adjust based on the maximum allowed by the API
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{primary_url}/klines", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_price_dip_to_threshold(price_data, threshold=0.60):
    """
    Checks if the price dipped to or below the threshold.
    
    Args:
        price_data (list): List of price data.
        threshold (float): Price threshold to check.
    
    Returns:
        bool: True if price dipped to or below the threshold, False otherwise.
    """
    for candle in price_data:
        # Assuming the 'L' price is at index 3 (low price of the candle)
        if float(candle[3]) <= threshold:
            return True
    return False

def main():
    # Define the time range
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Convert to UTC and then to milliseconds since epoch
    start_time = int(start_date.astimezone(pytz.utc).timestamp() * 1000)
    end_time = int(end_date.astimezone(pytz.utc).timestamp() * 1000)
    
    # Fetch price data
    price_data = fetch_fartcoin_price_data(start_time, end_time)
    
    if price_data is None:
        print("recommendation: p4")  # Unable to fetch data
    else:
        # Check if the price dipped to $0.60 or lower
        if check_price_dip_to_threshold(price_data):
            print("recommendation: p2")  # Yes, it dipped to $0.60 or lower
        else:
            print("recommendation: p1")  # No, it did not dip to $0.60 or lower

if __name__ == "__main__":
    main()