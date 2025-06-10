import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

def fetch_price_from_dexscreener(start_time, end_time):
    """
    Fetches the price of HOUSE/SOL from Dexscreener API within the specified time range.
    Args:
        start_time (int): Start time in milliseconds.
        end_time (int): End time in milliseconds.
    Returns:
        float: The highest price of HOUSE/SOL found in the time range or None if not found.
    """
    url = "https://api.dexscreener.io/latest/dex/pairs/solana/gj5t6kjtw3gww7srmhei1ojckayhyvlwb17gktf96hnh"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        for candle in data['pair']['1m']:
            if candle['time'] >= start_time and candle['time'] <= end_time:
                if float(candle['H']) >= 0.10000:
                    return float(candle['H'])
    except requests.RequestException as e:
        print(f"Failed to fetch data from Dexscreener: {e}")
    return None

def main():
    # Define the time range
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    start_time_ms = int(start_date.timestamp() * 1000)
    end_time_ms = int(end_date.timestamp() * 1000)

    # Fetch the price
    highest_price = fetch_price_from_dexscreener(start_time_ms, end_time_ms)

    # Determine the resolution based on the highest price found
    if highest_price is not None and highest_price >= 0.10000:
        print("recommendation: p2")  # Yes, the price reached $0.100 or higher
    else:
        print("recommendation: p1")  # No, the price did not reach $0.100

if __name__ == "__main__":
    main()