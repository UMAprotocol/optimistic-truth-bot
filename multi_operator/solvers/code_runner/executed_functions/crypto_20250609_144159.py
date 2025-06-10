import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Constants for the API endpoint and the specific cryptocurrency pair
DEXSCREENER_URL = "https://dexscreener.com/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
TIMEZONE = "US/Eastern"
START_DATE = "2025-04-23 10:00:00"
END_DATE = "2025-04-30 23:59:00"
TARGET_PRICE = 1.50

def fetch_data(url):
    """
    Fetch data from the Dexscreener API.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return None

def check_price_target(data, target_price):
    """
    Check if the price of Fartcoin reached the target price within the specified time frame.
    """
    for item in data['pairs']:
        for candle in item['chart']:
            if candle['h'] >= target_price:
                return True
    return False

def convert_to_utc(date_str, timezone_str):
    """
    Convert local time to UTC time.
    """
    local_tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    local_dt = local_tz.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    """
    Main function to process the market resolution based on the Fartcoin price data.
    """
    start_utc = convert_to_utc(START_DATE, TIMEZONE)
    end_utc = convert_to_utc(END_DATE, TIMEZONE)
    
    # Construct the URL with the appropriate query parameters for the time range
    url = f"{DEXSCREENER_URL}?startTime={start_utc}&endTime={end_utc}"
    
    data = fetch_data(url)
    if data is None:
        print("recommendation: p4")  # Unable to resolve due to data fetch failure
        return
    
    if check_price_target(data, TARGET_PRICE):
        print("recommendation: p2")  # Yes, price reached $1.50 or higher
    else:
        print("recommendation: p1")  # No, price did not reach $1.50

if __name__ == "__main__":
    main()