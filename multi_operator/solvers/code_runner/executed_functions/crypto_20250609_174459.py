import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Define the API endpoint for Dexscreener
DEXSCREENER_API_URL = "https://api.dexscreener.io/latest/dex/tokens"

# Define the time range for checking the Fartcoin price
START_DATE = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
END_DATE = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))

def fetch_fartcoin_prices():
    """
    Fetches the Fartcoin prices from Dexscreener API and checks if it reached $2.00 or higher.
    """
    # Convert datetime to timestamp in milliseconds
    start_timestamp = int(START_DATE.timestamp() * 1000)
    end_timestamp = int(END_DATE.timestamp() * 1000)

    params = {
        "pairAddress": "bzc9nzfmqkxr6fz1dbph7bdf9broyef6pnzesp7v5iiw",
        "from": start_timestamp,
        "to": end_timestamp,
        "interval": "1m"
    }

    try:
        response = requests.get(DEXSCREENER_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        # Check if any 1-minute candle "H" price reached $2.00 or higher
        for candle in data['data']['pair']['candles']:
            if float(candle['h']) >= 2.00:
                return True
        return False
    except requests.RequestException as e:
        print(f"Failed to fetch data from Dexscreener: {e}")
        return None

def main():
    result = fetch_fartcoin_prices()
    if result is True:
        print("recommendation: p2")  # Yes, Fartcoin reached $2.00 or higher
    elif result is False:
        print("recommendation: p1")  # No, Fartcoin did not reach $2.00
    else:
        print("recommendation: p3")  # Unknown or API error

if __name__ == "__main__":
    main()