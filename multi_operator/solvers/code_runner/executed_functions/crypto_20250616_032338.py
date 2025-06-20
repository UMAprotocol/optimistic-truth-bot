import requests
import logging
from datetime import datetime, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def fetch_metaplanet_btc_holdings():
    """
    Fetches the latest BTC holdings announcement from Metaplanet's official sources.
    Returns:
        The number of BTC held as an integer or None if data cannot be fetched.
    """
    # Placeholder URL for Metaplanet's official announcements
    url = "https://api.metaplanet.com/btc_holdings"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        btc_held = int(data['btc_held'])
        logger.info(f"Successfully retrieved BTC holdings: {btc_held}")
        return btc_held
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch BTC holdings: {e}")
        return None

def determine_market_resolution(btc_held):
    """
    Determines the market resolution based on BTC holdings.
    Args:
        btc_held: The number of BTC held by Metaplanet.
    Returns:
        A string indicating the market resolution.
    """
    if btc_held is None:
        return "p3"  # Unknown/50-50 if data cannot be fetched
    elif btc_held >= 10000:
        return "p2"  # Yes, Metaplanet holds 10,000 or more BTC
    else:
        return "p1"  # No, Metaplanet does not hold 10,000 BTC

def main():
    """
    Main function to handle the resolution of the market based on Metaplanet's BTC holdings.
    """
    logger.info("Fetching Metaplanet's BTC holdings...")
    btc_held = fetch_metaplanet_btc_holdings()
    resolution = determine_market_resolution(btc_held)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()