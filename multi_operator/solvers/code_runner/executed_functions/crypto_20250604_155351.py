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

# Constants for the market analysis
DEXSCREENER_URL = "https://dexscreener.com/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
START_DATE = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
END_DATE = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
TARGET_PRICE = 0.80

def fetch_dexscreener_data():
    """
    Fetches the historical price data for Fartcoin/SOL from Dexscreener.
    Checks if the price dipped to $0.80 or lower between the specified dates.
    """
    try:
        # Construct the URL with the appropriate parameters for the API call
        response = requests.get(DEXSCREENER_URL)
        response.raise_for_status()
        data = response.json()

        # Analyze the data to check for the price condition
        for candle in data['data']:
            if candle['L'] <= TARGET_PRICE:
                logger.info(f"Price dipped to {candle['L']} on {candle['date']}")
                return "p2"  # Corresponds to "Yes"
        
        logger.info("Price did not dip to $0.80 or lower.")
        return "p1"  # Corresponds to "No"
    
    except requests.RequestException as e:
        logger.error(f"Failed to fetch data from Dexscreener: {e}")
        return "p3"  # Corresponds to unknown/50-50 due to data fetch failure

def main():
    """
    Main function to handle the resolution of the market based on Dexscreener data.
    """
    result = fetch_dexscreener_data()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()