import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# Constants for API endpoints
DEXSCREENER_API_URL = "https://api.dexscreener.io/latest/dex/tokens"
DEXSCREENER_PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/dexscreener-proxy"

def fetch_price_data(token_pair_id, start_time, end_time):
    """
    Fetches price data from Dexscreener API with a fallback to a proxy server.
    Args:
        token_pair_id (str): The token pair ID for which to fetch the data.
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.
    Returns:
        float: The highest price found in the given time range or None if no data.
    """
    params = {
        "pairAddress": token_pair_id,
        "from": start_time,
        "to": end_time,
        "interval": "1m"
    }
    try:
        # Try fetching from the proxy first
        response = requests.get(DEXSCREENER_PROXY_URL, params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Proxy failed with error {e}, trying primary API endpoint.")
        try:
            # Fallback to the primary API endpoint
            response = requests.get(DEXSCREENER_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Both proxy and primary API requests failed: {e}")
            return None

    # Parse the data to find the highest price
    highest_price = 0
    for candle in data.get('data', []):
        if candle['h'] > highest_price:
            highest_price = candle['h']

    return highest_price if highest_price > 0 else None

def check_price_threshold(token_pair_id, start_date, end_date, threshold):
    """
    Checks if the price of a token pair has reached a certain threshold between two dates.
    Args:
        token_pair_id (str): The token pair ID.
        start_date (str): Start date in YYYY-MM-DD format.
        end_date (str): End date in YYYY-MM-DD format.
        threshold (float): Price threshold to check.
    Returns:
        str: Recommendation based on whether the threshold was reached.
    """
    # Convert dates to timestamps
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    start_timestamp = int(start_dt.replace(tzinfo=pytz.UTC).timestamp() * 1000)
    end_timestamp = int(end_dt.replace(tzinfo=pytz.UTC).timestamp() * 1000)

    # Fetch the price data
    highest_price = fetch_price_data(token_pair_id, start_timestamp, end_timestamp)

    # Determine the recommendation based on the highest price found
    if highest_price is None:
        return "recommendation: p4"  # Unable to determine due to API failure
    elif highest_price >= threshold:
        return "recommendation: p2"  # Yes, the price reached the threshold
    else:
        return "recommendation: p1"  # No, the price did not reach the threshold

def main():
    # Token pair ID for HOUSE/SOL on Dexscreener
    token_pair_id = "gj5t6kjtw3gww7srmhei1ojckayhyvlwb17gktf96hnh"
    # Date range and price threshold from the ancillary data
    start_date = "2025-05-07"
    end_date = "2025-05-31"
    price_threshold = 0.10000

    # Check if the price threshold was reached and print the result
    result = check_price_threshold(token_pair_id, start_date, end_date, price_threshold)
    print(result)

if __name__ == "__main__":
    main()