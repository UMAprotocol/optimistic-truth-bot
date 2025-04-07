import requests
from datetime import datetime
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def get_doge_close_price_at_specific_time():
    """
    Fetches the 1-minute candle close price for DOGEUSDT on Binance
    at noon on April 4, 2025, Eastern Time.

    Returns:
        Close price as float and a recommendation based on the price
    """
    # Define the date and time for the query
    date_str = "2025-04-04"
    hour = 12  # Noon
    minute = 0
    timezone_str = "US/Eastern"

    # Convert local time to UTC for the API request
    tz = pytz.timezone(timezone_str)
    time_str = f"{hour:02d}:{minute:02d}:00"
    target_time_local = tz.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(pytz.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)

    # Set parameters for the API request
    params = {
        "symbol": "DOGEUSDT",
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

    # Extract the close price
    close_price = float(data[0][4])

    # Determine the recommendation based on the close price
    recommendation = "p2" if close_price >= 0.18001 else "p1"
    return close_price, recommendation

def main():
    try:
        close_price, recommendation = get_doge_close_price_at_specific_time()
        print(f"DOGEUSDT close price on 2025-04-04 at 12:00 ET: {close_price}")
        print(f"recommendation: {recommendation}")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()