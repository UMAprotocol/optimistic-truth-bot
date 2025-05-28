import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Constants for the API endpoint and the threshold value
API_ENDPOINT = "https://data.hashrateindex.com/network-data/bitcoin-hashprice-index"
THRESHOLD_VALUE = 57.50001

def fetch_hashprice_data(start_date, end_date):
    """
    Fetches the Bitcoin Hashprice data from the Hashrate Index API within the specified date range.
    
    Args:
        start_date (datetime): The start date for the data fetch.
        end_date (datetime): The end date for the data fetch.
    
    Returns:
        list: A list of hashprice data points.
    """
    # Convert datetime to the format required by the API (if needed)
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())

    # Prepare the request parameters
    params = {
        "start": start_timestamp,
        "end": end_timestamp,
        "currency": "USD",
        "unit": "PH/s"
    }

    # Make the API request
    try:
        response = requests.get(API_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return None

def check_threshold(data):
    """
    Checks if any data point in the provided list exceeds the threshold value.
    
    Args:
        data (list): List of hashprice data points.
    
    Returns:
        bool: True if any data point exceeds the threshold, False otherwise.
    """
    for point in data:
        if point['price'] >= THRESHOLD_VALUE:
            return True
    return False

def main():
    # Define the time range for the data fetch
    start_date = datetime(2025, 5, 19, 18, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, 59, tzinfo=pytz.timezone('US/Eastern'))

    # Fetch the hashprice data
    data = fetch_hashprice_data(start_date, end_date)

    # Check if the threshold is exceeded
    if data and check_threshold(data):
        print("recommendation: p2")  # Yes, threshold exceeded
    else:
        print("recommendation: p1")  # No, threshold not exceeded

if __name__ == "__main__":
    main()