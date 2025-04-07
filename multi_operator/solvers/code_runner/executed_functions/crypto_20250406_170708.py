import requests
from datetime import datetime
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def get_xrp_close_price_at_specific_time():
    """
    Fetches the 1-minute candle close price for XRPUSDT on Binance
    at noon on April 4, 2025, Eastern Time.

    Returns:
        Close price as float
    """
    date_str = "2025-04-04"
    hour = 12
    minute = 0
    timezone_str = "US/Eastern"
    
    tz = pytz.timezone(timezone_str)
    time_str = f"{hour:02d}:{minute:02d}:00"
    target_time_local = tz.localize(
        datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    )
    target_time_utc = target_time_local.astimezone(pytz.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)

    params = {
        "symbol": "XRPUSDT",
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
    try:
        close_price = get_xrp_close_price_at_specific_time()
        threshold_price = 2.30001
        if close_price >= threshold_price:
            result = "Yes"
            recommendation = "p2"
        else:
            result = "No"
            recommendation = "p1"
        print(f"XRP price on 2025-04-04 at 12:00 ET: {close_price} (Threshold: {threshold_price}) - {result}")
        print(f"recommendation: {recommendation}")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("recommendation: p3")

if __name__ == "__main__":
    main()