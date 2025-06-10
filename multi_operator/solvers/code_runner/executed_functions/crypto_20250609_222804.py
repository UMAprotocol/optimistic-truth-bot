import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Constants for the API endpoints and the specific cryptocurrency pair
DEXSCREENER_URL = "https://dexscreener.com/solana/bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw"
FARTCOIN_SYMBOL = "Fartcoin/SOL"
START_DATE = "2025-05-07 15:00:00"
END_DATE = "2025-05-31 23:59:00"
TARGET_PRICE = 0.20
TIMEZONE = "US/Eastern"

def fetch_price_data():
    """
    Fetches the price data for Fartcoin from Dexscreener and checks if the price
    dipped to $0.20 or below between the specified start and end dates.
    """
    # Convert dates to UTC for accurate querying
    tz = pytz.timezone(TIMEZONE)
    start_dt = tz.localize(datetime.strptime(START_DATE, "%Y-%m-%d %H:%M:%S")).astimezone(pytz.utc)
    end_dt = tz.localize(datetime.strptime(END_DATE, "%Y-%m-%d %H:%M:%S")).astimezone(pytz.utc)

    # Prepare parameters for the API request
    params = {
        "pair": FARTCOIN_SYMBOL,
        "interval": "1m",
        "start": int(start_dt.timestamp() * 1000),  # Convert to milliseconds
        "end": int(end_dt.timestamp() * 1000)
    }

    try:
        # Make the request to Dexscreener
        response = requests.get(DEXSCREENER_URL, params=params)
        response.raise_for_status()
        data = response.json()

        # Check each candle to see if the price dipped to $0.20 or below
        for candle in data['candles']:
            if candle['L'] <= TARGET_PRICE:
                return True
        return False
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return None

def main():
    """
    Main function to determine the resolution of the prediction market.
    """
    result = fetch_price_data()
    if result is True:
        print("recommendation: p2")  # Yes, the price dipped to $0.20 or below
    elif result is False:
        print("recommendation: p1")  # No, the price did not dip to $0.20 or below
    else:
        print("recommendation: p3")  # Unknown or data fetch error

if __name__ == "__main__":
    main()