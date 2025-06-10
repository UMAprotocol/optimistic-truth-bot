import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

def fetch_price_from_dexscreener():
    """
    Fetches the price of HOUSE/SOL from Dexscreener.
    """
    url = "https://dexscreener.com/solana/gj5t6kjtw3gww7srmhei1ojckayhyvlwb17gktf96hnh"
    params = {
        "pair": "HOUSE/SOL",
        "interval": "1m"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Error fetching data from Dexscreener: {e}")
        return None

def check_price_threshold(data, threshold=0.150):
    """
    Checks if any 1-minute candle 'H' price reached or exceeded the threshold.
    """
    for candle in data:
        if candle['H'] >= threshold:
            return True
    return False

def main():
    """
    Main function to determine if HOUSE/SOL reached $0.150 on Dexscreener.
    """
    data = fetch_price_from_dexscreener()
    if data is None:
        print("recommendation: p4")  # Unable to fetch data
        return

    result = check_price_threshold(data)
    if result:
        print("recommendation: p2")  # Yes, it reached $0.150
    else:
        print("recommendation: p1")  # No, it did not reach $0.150

if __name__ == "__main__":
    main()