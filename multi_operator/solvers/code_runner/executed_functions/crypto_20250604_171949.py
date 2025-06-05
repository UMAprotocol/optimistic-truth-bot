import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Define the API endpoint for the Hashrate Index
HASHRATE_INDEX_URL = "https://data.hashrateindex.com/network-data/bitcoin-hashprice-index"

def fetch_hashprice_data(start_date, end_date):
    """
    Fetches the Bitcoin Hashprice data from the Hashrate Index within the specified date range.
    
    Args:
        start_date (datetime): The start date for the data fetch.
        end_date (datetime): The end date for the data fetch.
    
    Returns:
        list: A list of hashprice data points.
    """
    params = {
        "start": int(start_date.timestamp()),
        "end": int(end_date.timestamp()),
        "resolution": "3M",
        "currency": "USD",
        "unit": "PH/s"
    }
    try:
        response = requests.get(HASHRATE_INDEX_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch data: {str(e)}")
        return None

def check_hashprice_threshold(data, threshold=60.00001):
    """
    Checks if any hashprice in the data exceeds the specified threshold.
    
    Args:
        data (list): List of hashprice data points.
        threshold (float): The price threshold to check against.
    
    Returns:
        bool: True if any data point exceeds the threshold, False otherwise.
    """
    for entry in data:
        if entry['price'] >= threshold:
            return True
    return False

def main():
    # Define the time range for the query
    start_date = datetime(2025, 5, 19, 18, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Fetch the hashprice data
    data = fetch_hashprice_data(start_date, end_date)
    
    if data is None:
        print("recommendation: p4")  # Unable to resolve due to data fetch failure
        return
    
    # Check if the hashprice ever reaches or exceeds $60.00001
    if check_hashprice_threshold(data):
        print("recommendation: p2")  # Yes, it reaches the threshold
    else:
        print("recommendation: p1")  # No, it does not reach the threshold

if __name__ == "__main__":
    main()