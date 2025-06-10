import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys are not required for this specific task as we are accessing public data from Dexscreener
# However, if needed for other purposes, they can be loaded as shown:
# BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

def fetch_housecoin_prices(start_date, end_date):
    """
    Fetches the 1-minute candle data for Housecoin (HOUSE/SOL) from Dexscreener between specified dates.
    
    Args:
        start_date (datetime): Start date and time in ET timezone.
        end_date (datetime): End date and time in ET timezone.
    
    Returns:
        bool: True if price reached or exceeded $0.100, False otherwise.
    """
    # Convert times to UTC as Dexscreener API requires UTC
    start_date_utc = start_date.astimezone(pytz.utc)
    end_date_utc = end_date.astimezone(pytz.utc)

    # Format timestamps for URL (Dexscreener uses milliseconds)
    start_timestamp = int(start_date_utc.timestamp() * 1000)
    end_timestamp = int(end_date_utc.timestamp() * 1000)

    # Construct the URL for Dexscreener API
    url = f"https://dexscreener.com/solana/gj5t6kjtw3gww7srmhei1ojckayhyvlwb17gktf96hnh?from={start_timestamp}&to={end_timestamp}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Check each candle to see if the final "H" price reached $0.10000 or higher
        for candle in data['data']['pairs'][0]['chart']:
            if float(candle['h']) >= 0.10000:
                return True
        return False
    except Exception as e:
        print(f"Failed to fetch or process data: {e}")
        return False

def main():
    # Define the time period to check
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone("America/New_York"))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone("America/New_York"))

    # Fetch prices and determine if the condition was met
    price_reached = fetch_housecoin_prices(start_date, end_date)

    # Print the result based on the condition
    if price_reached:
        print("recommendation: p2")  # Yes, price reached $0.100
    else:
        print("recommendation: p1")  # No, price did not reach $0.100

if __name__ == "__main__":
    main()