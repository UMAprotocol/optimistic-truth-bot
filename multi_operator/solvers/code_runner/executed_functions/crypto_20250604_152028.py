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

def fetch_price_from_dexscreener(start_time, end_time):
    """
    Fetches the price data for HOUSE/SOL from Dexscreener API within the specified time range.

    Args:
        start_time: Start time in milliseconds since epoch.
        end_time: End time in milliseconds since epoch.

    Returns:
        True if price reached or exceeded $0.250, False otherwise.
    """
    url = "https://api.dexscreener.io/latest/dex/pairs/solana/gj5t6kjtw3gww7srmhei1ojckayhyvlwb17gktf96hnh"
    params = {
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        for candle in data['pair']['1m']:
            if float(candle['H']) >= 0.250:
                return True
        return False
    except Exception as e:
        logger.error(f"Failed to fetch or parse data from Dexscreener: {e}")
        return False

def convert_to_utc_timestamp(date_str, time_str, timezone_str):
    """
    Converts local time to UTC timestamp in milliseconds.

    Args:
        date_str: Date in YYYY-MM-DD format.
        time_str: Time in HH:MM format.
        timezone_str: Timezone string.

    Returns:
        UTC timestamp in milliseconds.
    """
    tz = pytz.timezone(timezone_str)
    local_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_dt = tz.localize(local_time)
    utc_dt = local_dt.astimezone(pytz.utc)
    return int(utc_dt.timestamp() * 1000)

def main():
    """
    Main function to check if HOUSE/SOL price reached $0.250 between May 7, 2025, 15:00 and May 31, 2025, 23:59 ET.
    """
    start_time = convert_to_utc_timestamp("2025-05-07", "15:00", "US/Eastern")
    end_time = convert_to_utc_timestamp("2025-05-31", "23:59", "US/Eastern")
    
    if fetch_price_from_dexscreener(start_time, end_time):
        print("recommendation: p2")  # Yes, price reached $0.250
    else:
        print("recommendation: p1")  # No, price did not reach $0.250

if __name__ == "__main__":
    main()