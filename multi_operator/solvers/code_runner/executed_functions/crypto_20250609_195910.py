import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

def fetch_hashprice_data(start_date, end_date):
    """
    Fetches Bitcoin Hashprice data from the Hashrate Index API within the specified date range.
    
    Args:
        start_date (datetime): Start date of the period to fetch data for.
        end_date (datetime): End date of the period to fetch data for.
    
    Returns:
        list: List of hashprice data points.
    """
    url = "https://data.hashrateindex.com/network-data/bitcoin-hashprice-index"
    params = {
        "start": int(start_date.timestamp()),
        "end": int(end_date.timestamp()),
        "currency": "USD",
        "hashrateUnit": "PH/s",
        "interval": "3M"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return None

def check_price_dip_to_threshold(data, threshold):
    """
    Checks if the price in any data point dips to or below the threshold.
    
    Args:
        data (list): List of hashprice data points.
        threshold (float): Price threshold to check against.
    
    Returns:
        bool: True if any data point meets the condition, False otherwise.
    """
    for point in data:
        if point['price'] <= threshold:
            return True
    return False

def main():
    # Define the time period and threshold based on the market's ancillary data
    start_date = datetime(2025, 5, 19, 18, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    threshold = 52.49999

    # Fetch the hashprice data
    data = fetch_hashprice_data(start_date, end_date)

    # Check if the price dips to or below the threshold
    if data and check_price_dip_to_threshold(data, threshold):
        print("recommendation: p2")  # Yes, the price dipped to $52.50 or lower
    else:
        print("recommendation: p1")  # No, the price did not dip to $52.50 or lower

if __name__ == "__main__":
    main()