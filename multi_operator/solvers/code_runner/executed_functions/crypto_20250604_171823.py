import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Define API endpoints
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_hashprice_data(start_time, end_time):
    """
    Fetches the Bitcoin Hashprice data from the Hashrate Index API within the specified timeframe.
    Args:
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.
    Returns:
        list: List of hashprice data points.
    """
    url = "https://data.hashrateindex.com/network-data/bitcoin-hashprice-index"
    params = {
        "start": start_time,
        "end": end_time,
        "currency": "USD",
        "hashrate_units": "PH/s"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return None

def check_hashprice_threshold(data, threshold=60.00001):
    """
    Checks if any hashprice in the data exceeds the specified threshold.
    Args:
        data (list): List of hashprice data points.
        threshold (float): Threshold value to check against.
    Returns:
        bool: True if any hashprice exceeds the threshold, False otherwise.
    """
    for entry in data:
        if entry['price'] >= threshold:
            return True
    return False

def main():
    # Define the timeframe for the query
    start_date = datetime(2025, 5, 19, 18, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Convert dates to UTC and then to milliseconds since epoch
    start_time_ms = int(start_date.astimezone(pytz.utc).timestamp() * 1000)
    end_time_ms = int(end_date.astimezone(pytz.utc).timestamp() * 1000)
    
    # Fetch hashprice data
    data = fetch_hashprice_data(start_time_ms, end_time_ms)
    
    # Check if any hashprice exceeds the threshold
    if data and check_hashprice_threshold(data):
        print("recommendation: p2")  # Yes, hashprice reached $60.00 or higher
    else:
        print("recommendation: p1")  # No, hashprice did not reach $60.00

if __name__ == "__main__":
    main()