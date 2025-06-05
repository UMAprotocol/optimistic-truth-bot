import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# Constants
DEXSCREENER_URL = "https://dexscreener.com/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
START_DATE = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
END_DATE = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
TARGET_PRICE = 0.90

def fetch_data():
    # Calculate the timestamps for the start and end dates
    start_timestamp = int(START_DATE.timestamp())
    end_timestamp = int(END_DATE.timestamp())

    # Prepare the parameters for the API request
    params = {
        'start': start_timestamp,
        'end': end_timestamp,
        'interval': '1m'
    }

    # Make the request to Dexscreener
    try:
        response = requests.get(DEXSCREENER_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return None

def analyze_data(data):
    # Check if any 'L' price in the data dips to $0.90 or lower
    for candle in data['data']:
        if float(candle['L']) <= TARGET_PRICE:
            return "p2"  # Yes, it dipped to $0.90 or lower
    return "p1"  # No, it did not dip to $0.90

def main():
    data = fetch_data()
    if data:
        recommendation = analyze_data(data)
        print(f"recommendation: {recommendation}")
    else:
        print("recommendation: p4")  # Unable to resolve due to data fetch failure

if __name__ == "__main__":
    main()