import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the API endpoints
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_hashprice_data(start_date, end_date):
    """
    Fetches the Bitcoin Hashprice data from the Hashrate Index within the specified date range.
    Args:
        start_date (datetime): Start date of the period to fetch data for.
        end_date (datetime): End date of the period to fetch data for.
    Returns:
        list: List of hashprice data points.
    """
    # Convert dates to the appropriate format for the API
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)

    # Construct the URL with the required parameters
    url = f"{PROXY_ENDPOINT}?symbol=BTCUSDT&interval=1d&startTime={start_timestamp}&endTime={end_timestamp}"

    try:
        # First attempt to use the proxy endpoint
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        url = f"{PRIMARY_ENDPOINT}/klines?symbol=BTCUSDT&interval=1d&startTime={start_timestamp}&endTime={end_timestamp}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

def check_hashprice_threshold(data, threshold=60.00001):
    """
    Checks if any hashprice in the data exceeds the specified threshold.
    Args:
        data (list): List of hashprice data points.
        threshold (float): Threshold value to check against.
    Returns:
        bool: True if any data point exceeds the threshold, False otherwise.
    """
    for item in data:
        if float(item[4]) >= threshold:  # Assuming the closing price is the relevant value
            return True
    return False

def main():
    # Define the time period for the query
    start_date = datetime(2025, 5, 19, 18, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))

    # Fetch the hashprice data
    data = fetch_hashprice_data(start_date, end_date)

    # Check if the hashprice exceeded the threshold
    if check_hashprice_threshold(data):
        print("recommendation: p2")  # Yes, it reached $60.00 or higher
    else:
        print("recommendation: p1")  # No, it did not reach $60.00

if __name__ == "__main__":
    main()