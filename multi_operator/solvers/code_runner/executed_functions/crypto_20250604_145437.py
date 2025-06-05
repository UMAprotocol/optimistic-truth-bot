import requests
import logging
from datetime import datetime, timedelta, timezone
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

def fetch_fartcoin_price():
    """
    Fetches the Fartcoin/SOL price data from Dexscreener and checks if it reached $3.00 or higher.
    """
    # Define the URL and parameters for the Dexscreener API
    url = "https://dexscreener.com/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
    params = {
        "interval": "1m",
        "startTime": int(datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern')).timestamp() * 1000),
        "endTime": int(datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern')).timestamp() * 1000)
    }

    try:
        # Make the HTTP request to Dexscreener
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Check if any 1-minute candle's final "H" price reached $3.00 or higher
        for candle in data['data']:
            if float(candle['H']) >= 3.00:
                logger.info("Fartcoin reached $3.00 or higher.")
                return "p2"  # Yes, it reached $3.00 or higher
        logger.info("Fartcoin did not reach $3.00.")
        return "p1"  # No, it did not reach $3.00

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from Dexscreener: {e}")
        return "p3"  # Unknown/50-50 due to error

def main():
    """
    Main function to handle the resolution of the market based on Fartcoin prices.
    """
    resolution = fetch_fartcoin_price()
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()