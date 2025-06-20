import requests
import logging
from datetime import datetime, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def get_btc_holdings():
    """
    Fetches the latest BTC holdings announcement from Metaplanet.
    Returns:
        The number of BTC held as an integer, or None if the data cannot be retrieved.
    """
    # Placeholder URL for Metaplanet's announcements (this should be replaced with the actual URL)
    announcement_url = "https://metaplanet.com/api/btc-holdings"
    
    try:
        response = requests.get(announcement_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        btc_held = int(data['btc_held'])
        logger.info(f"Successfully retrieved BTC holdings: {btc_held}")
        return btc_held
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch BTC holdings: {e}")
        return None

def check_btc_threshold():
    """
    Checks if Metaplanet holds 10,000 or more BTC.
    Returns:
        'p2' if Metaplanet holds 10,000 or more BTC,
        'p1' if Metaplanet holds less than 10,000 BTC,
        'p3' if the data is unknown or the request fails.
    """
    btc_held = get_btc_holdings()
    if btc_held is None:
        return "p3"  # Unknown
    elif btc_held >= 10000:
        return "p2"  # Yes
    else:
        return "p1"  # No

def main():
    """
    Main function to determine if Metaplanet holds 10,000 or more BTC.
    """
    result = check_btc_threshold()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()