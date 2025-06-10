import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Constants for the API endpoints
DEXSCREENER_API_URL = "https://dexscreener.com/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"

def fetch_fartcoin_data(start_time, end_time):
    """
    Fetches Fartcoin data from Dexscreener API within the specified time range.
    
    Args:
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.
    
    Returns:
        list: List of data points containing price information.
    """
    params = {
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        response = requests.get(DEXSCREENER_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return None

def check_price_threshold(data, threshold=1.50):
    """
    Checks if the price of Fartcoin exceeded the threshold at any point in the data.
    
    Args:
        data (list): List of data points from Dexscreener.
        threshold (float): Price threshold to check against.
    
    Returns:
        bool: True if the price exceeded the threshold, False otherwise.
    """
    for point in data:
        if point['H'] >= threshold:
            return True
    return False

def main():
    # Define the time range for the query
    start_date = datetime(2025, 4, 23, 10, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 4, 30, 23, 59, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Convert datetime to milliseconds since epoch
    start_time_ms = int(start_date.timestamp() * 1000)
    end_time_ms = int(end_date.timestamp() * 1000)
    
    # Fetch data from Dexscreener
    data = fetch_fartcoin_data(start_time_ms, end_time_ms)
    
    if data is None:
        print("recommendation: p4")  # Unable to fetch data
        return
    
    # Check if the price exceeded the threshold
    if check_price_threshold(data):
        print("recommendation: p2")  # Yes, price exceeded $1.50
    else:
        print("recommendation: p1")  # No, price did not exceed $1.50

if __name__ == "__main__":
    main()