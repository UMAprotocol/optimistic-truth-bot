import requests
from datetime import datetime
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def get_close_price_at_specific_time(date_str, hour=12, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the 1-minute candle close price for BTCUSDT on Binance
    at a specific time on a given date.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format (default: 12)
        minute: Minute (default: 0)
        timezone_str: Timezone string (default: "US/Eastern")

    Returns:
        Close price as float
    """
    tz = pytz.timezone(timezone_str)
    time_str = f"{hour:02d}:{minute:02d}:00"
    target_time_local = tz.localize(
        datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    )
    target_time_utc = target_time_local.astimezone(pytz.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)

    params = {
        "symbol": "BTCUSDT",
        "interval": "1m",
        "limit": 1,
        "startTime": start_time_ms,
        "endTime": start_time_ms + 60000  # plus 1 minute
    }

    response = requests.get("https://api.binance.com/api/v3/klines", params=params)
    response.raise_for_status()  # Will raise an exception for HTTP errors
    data = response.json()

    if not data:
        raise Exception(f"No data returned for {date_str} {time_str} {timezone_str}")

    close_price = float(data[0][4])
    return close_price

def main():
    # Dates and times are hardcoded based on the specific question requirements
    date1 = "2025-03-20"
    date2 = "2025-03-21"
    hour = 12
    minute = 0
    timezone_str = "US/Eastern"

    try:
        price_1 = get_close_price_at_specific_time(date1, hour, minute, timezone_str)
        price_2 = get_close_price_at_specific_time(date2, hour, minute, timezone_str)

        if price_1 < price_2:
            result = "Up"
            recommendation = "recommendation: p2"
        elif price_1 > price_2:
            result = "Down"
            recommendation = "recommendation: p1"
        else:
            result = "50-50"
            recommendation = "recommendation: p3"

        print(f"BTC price on {date1} at {hour}:{minute} {timezone_str}: {price_1}")
        print(f"BTC price on {date2} at {hour}:{minute} {timezone_str}: {price_2}")
        print(f"Market resolves to: {result}")
        print(recommendation)

    except Exception as e:
        print(f"Error occurred: {e}")
        print("recommendation: p4")

if __name__ == "__main__":
    main()