import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def check_eth_price_dip():
    """
    Checks if the Ethereum price on Binance dipped to $1,500 or lower
    between December 30, 2024, 21:00 and December 31, 2025, 23:59 ET.
    """
    # Define the symbol and the interval for the API request
    symbol = "ETHUSDT"
    interval = "1m"
    # Timezone conversion for Eastern Time
    tz = pytz.timezone("US/Eastern")
    start_time_local = tz.localize(datetime(2024, 12, 30, 21, 0, 0))
    end_time_local = tz.localize(datetime(2025, 12, 31, 23, 59, 0))
    # Convert local times to UTC for API request
    start_time_utc = int(start_time_local.astimezone(pytz.utc).timestamp() * 1000)
    end_time_utc = int(end_time_local.astimezone(pytz.utc).timestamp() * 1000)

    # Prepare API request parameters
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time_utc,
        "endTime": end_time_utc,
        "limit": 1000  # Maximum limit per API call
    }

    # API endpoint for historical klines
    url = "https://api.binance.com/api/v3/klines"

    try:
        # Loop through the time range in chunks, due to API limit constraints
        while start_time_utc < end_time_utc:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Check each candle if the low price is $1,500 or lower
            for candle in data:
                low_price = float(candle[3])
                if low_price <= 1500:
                    return "Yes"

            # Update start time for next API call
            last_candle_time = int(data[-1][6])
            params["startTime"] = last_candle_time + 1

        # If loop completes without finding a dip to $1,500 or lower
        return "No"
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Unknown"

def main():
    result = check_eth_price_dip()
    if result == "Yes":
        print("recommendation: p2")  # Yes, price dipped to $1,500 or lower
    elif result == "No":
        print("recommendation: p1")  # No, price did not dip to $1,500 or lower
    else:
        print("recommendation: p3")  # Unknown, due to an error

if __name__ == "__main__":
    main()