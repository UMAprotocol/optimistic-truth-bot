import requests
import logging
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Constants for the query
DEXSCREENER_URL = "https://dexscreener.com/solana/gj5t6kjtw3gww7srmhei1ojckayhyvlwb17gktf96hnh"
START_DATE = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
END_DATE = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
TARGET_PRICE = 0.01800

def fetch_data(url):
    """
    Fetch data from the given URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch data: {e}")
        return None

def check_price_dip(data, target_price):
    """
    Check if the price has dipped to or below the target price.
    """
    for candle in data['data']:
        if float(candle['L']) <= target_price:
            return True
    return False

def main():
    """
    Main function to process the data and determine the market resolution.
    """
    logger.info("Starting the price check process.")
    current_time = datetime.now(pytz.timezone('US/Eastern'))
    
    if current_time < START_DATE:
        logger.info("The monitoring period has not started yet.")
        print("recommendation: p4")
        return
    
    if current_time > END_DATE:
        logger.info("The monitoring period has ended.")
        data = fetch_data(DEXSCREENER_URL)
        if data and check_price_dip(data, TARGET_PRICE):
            print("recommendation: p2")  # Yes, price dipped to or below target
        else:
            print("recommendation: p1")  # No, price did not dip to or below target
    else:
        logger.info("The monitoring period is currently active.")
        print("recommendation: p4")

if __name__ == "__main__":
    main()