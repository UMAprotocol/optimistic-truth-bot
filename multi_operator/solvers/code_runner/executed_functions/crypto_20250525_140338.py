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

def fetch_hyperliquid_data(date_str, hour=12, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the 'Close' price for the HYPE/USDC pair from Hyperliquid at a specific time on a given date.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format (default: 12)
        minute: Minute (default: 0)
        timezone_str: Timezone string (default: "US/Eastern")

    Returns:
        Close price as float
    """
    logger.info(f"Fetching HYPE/USDC price for {date_str} at {hour}:{minute} {timezone_str}")
    
    # Convert the target time to UTC timestamp
    try:
        tz = pytz.timezone(timezone_str)
        time_str = f"{hour:02d}:{minute:02d}:00"
        target_time_local = tz.localize(
            datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        )
        target_time_utc = target_time_local.astimezone(timezone.utc)
        timestamp = int(target_time_utc.timestamp())
        
        logger.debug(f"Converted local time to UTC timestamp: {timestamp}")
    except Exception as e:
        logger.error(f"Error converting time: {e}")
        raise

    # Construct the URL to fetch data from Hyperliquid
    url = f"https://app.hyperliquid.xyz/trade/HYPE/USDC?interval=1m&timestamp={timestamp}"
    
    try:
        logger.debug(f"Requesting data from Hyperliquid: {url}")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data:
            close_price = float(data['close'])
            logger.info(f"Successfully retrieved close price: {close_price}")
            return close_price
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to Hyperliquid failed: {e}")
        raise

def main():
    """
    Main function to handle the resolution of the Hyperliquid market question.
    """
    # Dates and times for the price checks
    date1 = "2025-05-23"
    date2 = "2025-05-24"
    
    try:
        # Fetch close prices for both dates at 12:00 ET
        price1 = fetch_hyperliquid_data(date1)
        price2 = fetch_hyperliquid_data(date2)
        
        # Log the results
        logger.info(f"Close price on {date1} at 12:00 ET: {price1}")
        logger.info(f"Close price on {date2} at 12:00 ET: {price2}")
        
        # Determine the resolution based on the prices
        if price1 < price2:
            recommendation = "p2"  # Up
        elif price1 > price2:
            recommendation = "p1"  # Down
        else:
            recommendation = "p3"  # 50-50
        
        # Output the recommendation
        print(f"recommendation: {recommendation}")
        
    except Exception as e:
        logger.error(f"Error processing the market resolution: {e}")
        # Default to p4 (unknown) in case of any errors
        print("recommendation: p4")

if __name__ == "__main__":
    main()