import requests
from datetime import datetime
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def get_solana_close_price_at_specific_time():
    """
    Fetches the 1-minute candle close price for SOLUSDT on Binance
    at noon on April 4, 2025 in the Eastern Time timezone.

    Returns:
        Close price as float
    """
    # Define the date and time for the query
    date_str = "2025-04-04"
    hour = 12
    minute = 0
    timezone_str = "US/Eastern"

    # Convert local time to UTC for Binance API request
    tz = pytz.timezone(timezone_str)
    time_str = f"{hour:02d}:{minute:02d}:00"
    target_time_local = tz.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(pytz.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)

    # Set parameters for the API request
    params = {
        "symbol": "SOLUSDT",
        "interval": "1m",
        "limit": 1,
        "startTime": start_time_ms,
        "endTime": start_time_ms + 60000  # plus 1 minute
    }

    # Make the API request to Binance
    response = requests.get("https://api.binance.com/api/v3/klines", params=params)
    response.raise_for_status()  # Will raise an exception for HTTP errors
    data = response.json()

    # Check if data is returned
    if not data:
        raise Exception(f"No data returned for {date_str} {time_str} {timezone_str}")

    # Extract the close price from the data
    close_price = float(data[0][4])
    return close_price

def main():
    try:
        # Fetch the close price for SOLUSDT at the specified time
        close_price = get_solana_close_price_at_specific_time()
        print(f"Close price for SOLUSDT on 2025-04-04 at 12:00 ET: {close_price}")

        # Determine the market resolution based on the close price
        if close_price >= 130.01:
            print("recommendation: p2")  # Yes
        else:
            print("recommendation: p1")  # No
    except Exception as e:
        print(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50

if __name__ == "__main__":
    main()