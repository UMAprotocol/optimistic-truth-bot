import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# Constants for the API endpoints
DEXSCREENER_API_URL = "https://api.dexscreener.io/latest/dex/tokens"
HOUSE_SOL_PAIR_ID = "gj5t6kjtw3gww7srmhei1ojckayhyvlwb17gktf96hnh"

def fetch_price_data(pair_id):
    """
    Fetches price data for a specific trading pair from Dexscreener.
    """
    try:
        response = requests.get(f"{DEXSCREENER_API_URL}/{pair_id}")
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return None

def check_price_dip_to_threshold(data, threshold):
    """
    Checks if the price has dipped to or below a specified threshold.
    """
    try:
        for pair in data['pairs']:
            for candle in pair['candles']:
                if float(candle['l']) <= threshold:
                    return True
        return False
    except KeyError:
        print("Error processing data. Key not found.")
        return False
    except TypeError:
        print("Error processing data. Invalid data type encountered.")
        return False

def main():
    # Define the threshold price to check
    threshold_price = 0.02000

    # Fetch the price data
    price_data = fetch_price_data(HOUSE_SOL_PAIR_ID)

    if price_data is None:
        print("recommendation: p4")  # Unable to fetch data
    else:
        # Check if the price has dipped to or below the threshold
        if check_price_dip_to_threshold(price_data, threshold_price):
            print("recommendation: p2")  # Yes, price dipped to or below $0.020
        else:
            print("recommendation: p1")  # No, price did not dip to or below $0.020

if __name__ == "__main__":
    main()