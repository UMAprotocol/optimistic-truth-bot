import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_historical_high(symbol, start_time, end_time):
    """
    Fetch the highest price of a symbol between start_time and end_time using Binance API.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000  # Maximum limit
    }
    try:
        # Try proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}/klines", params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Proxy failed, trying primary endpoint: {e}")
        # Fallback to primary endpoint
        response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params)
        response.raise_for_status()
        data = response.json()

    # Extract the highest price from the data
    highest_price = max(float(candle[2]) for candle in data) if data else None
    return highest_price

def main():
    symbol = "DOGEUSDT"
    # Define the time range for May 2025 in ET timezone
    tz = pytz.timezone("US/Eastern")
    start_date = tz.localize(datetime(2025, 5, 1))
    end_date = tz.localize(datetime(2025, 5, 31, 23, 59))

    # Convert to UTC timestamps in milliseconds
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)

    # Fetch the highest price in May 2025
    highest_may_price = fetch_historical_high(symbol, start_time, end_time)

    # Fetch the highest price before May 2025
    highest_before_may_price = fetch_historical_high(symbol, 0, start_time)

    # Determine the resolution
    if highest_may_price is not None and highest_before_may_price is not None:
        if highest_may_price > highest_before_may_price:
            print("recommendation: p2")  # Yes, new all-time high in May
        else:
            print("recommendation: p1")  # No new all-time high in May
    else:
        print("recommendation: p4")  # Unable to determine

if __name__ == "__main__":
    main()