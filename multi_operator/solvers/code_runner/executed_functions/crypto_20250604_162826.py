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
    Fetches the lowest price of Fartcoin/SOL from Dexscreener within the specified date range.
    """
    # Define the time range for the query
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Convert to timestamps
    start_timestamp = int(start_date.timestamp() * 1000)  # milliseconds
    end_timestamp = int(end_date.timestamp() * 1000)  # milliseconds

    # Construct the URL for the API request
    url = f"{PROXY_URL}/api/v3/klines"
    params = {
        "symbol": "FARTSOL",
        "interval": "1m",
        "startTime": start_timestamp,
        "endTime": end_timestamp
    }

    try:
        # Try fetching from the proxy endpoint
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Proxy failed, trying primary endpoint: {e}")
        # Fallback to the primary endpoint
        url = f"{PRIMARY_URL}/klines"
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Both proxy and primary requests failed: {e}")
            return "recommendation: p4"

    # Check if any candle's low price is $0.75 or lower
    for candle in data:
        low_price = float(candle[3])  # Low price is the fourth element in the list
        if low_price <= 0.75:
            return "recommendation: p2"  # Yes, price dipped to $0.75 or lower

    return "recommendation: p1"  # No, price did not dip to $0.75 or lower

if __name__ == "__main__":
    result = fetch_price_from_dexscreener()
    print(result)