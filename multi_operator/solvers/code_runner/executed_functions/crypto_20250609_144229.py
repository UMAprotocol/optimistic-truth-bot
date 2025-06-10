import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Constants for the API endpoints and the Dexscreener URL
DEXSCREENER_URL = "https://dexscreener.com/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"

def fetch_fartcoin_data(start_time, end_time):
    """
    Fetches Fartcoin data from Dexscreener within the specified time range.
    
    Args:
        start_time (datetime): Start time in UTC.
        end_time (datetime): End time in UTC.
    
    Returns:
        bool: True if Fartcoin hit $1.50 or higher, False otherwise.
    """
    # Convert datetime to timestamps in milliseconds
    start_timestamp = int(start_time.timestamp() * 1000)
    end_timestamp = int(end_time.timestamp() * 1000)
    
    # Construct the URL with the appropriate parameters
    url = f"{DEXSCREENER_URL}?startTime={start_timestamp}&endTime={end_timestamp}&interval=1m"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Check if any 1-minute candle high price is 1.50 or higher
        for candle in data['data']:
            if candle['high'] >= 1.50:
                return True
        return False
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return False

def main():
    # Define the time range in Eastern Time
    start_time_et = datetime(2025, 4, 23, 10, 0, 0)
    end_time_et = datetime(2025, 4, 30, 23, 59, 59)
    
    # Convert Eastern Time to UTC
    eastern = pytz.timezone('US/Eastern')
    start_time_utc = eastern.localize(start_time_et).astimezone(pytz.utc)
    end_time_utc = eastern.localize(end_time_et).astimezone(pytz.utc)
    
    # Fetch data and determine the outcome
    result = fetch_fartcoin_data(start_time_utc, end_time_utc)
    
    # Print the recommendation based on the result
    if result:
        print("recommendation: p2")  # Yes, Fartcoin hit $1.50 or higher
    else:
        print("recommendation: p1")  # No, Fartcoin did not hit $1.50

if __name__ == "__main__":
    main()