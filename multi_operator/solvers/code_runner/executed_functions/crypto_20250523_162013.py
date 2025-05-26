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

def get_fartcoin_price():
    """
    Fetches the Fartcoin price for May 23, 2025 at 12:00 PM ET from Hyperliquid.
    """
    symbol = "FARTCOIN-USD"
    interval = "1m"
    date_str = "2025-05-23"
    hour = 12
    minute = 0
    timezone_str = "US/Eastern"

    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    time_str = f"{hour:02d}:{minute:02d}:00"
    target_time_local = tz.localize(
        datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    )
    target_time_utc = target_time_local.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)

    # Hyperliquid API URL
    api_url = "https://app.hyperliquid.xyz/api/v1/candles"
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time_ms,
        "endTime": start_time_ms + 60000  # plus 1 minute
    }

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data and 'candles' in data and data['candles']:
            close_price = float(data['candles'][0]['close'])
            logger.info(f"Successfully retrieved Fartcoin price: {close_price}")
            return close_price
        else:
            logger.error("No data returned from Hyperliquid for the specified time.")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def main():
    """
    Main function to determine if Fartcoin was above $1.40 on May 23, 2025 at 12:00 PM ET.
    """
    price = get_fartcoin_price()
    if price is None:
        print("recommendation: p3")  # Unknown/50-50 if no data could be fetched
    elif price >= 1.4001:
        print("recommendation: p2")  # Yes, Fartcoin was above $1.40
    else:
        print("recommendation: p1")  # No, Fartcoin was not above $1.40

if __name__ == "__main__":
    main()