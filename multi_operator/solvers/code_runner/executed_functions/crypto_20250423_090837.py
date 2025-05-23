import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance using both the proxy and primary endpoints with a fallback mechanism.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum allowed by Binance for one request
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_xrp_price_threshold(start_date, end_date, threshold):
    """
    Checks if the XRP price reached a given threshold at any point between start_date and end_date.
    """
    # Convert dates to timestamps
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)

    # Fetch price data
    data = fetch_price_data("XRPUSDT", start_timestamp, end_timestamp)

    if data:
        # Check if any high price meets or exceeds the threshold
        for candle in data:
            high_price = float(candle[2])  # High price is at index 2
            if high_price >= threshold:
                return True
    return False

def main():
    # Define the time period for the check
    start_date = datetime(2025, 4, 1, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_date = datetime(2025, 4, 30, 23, 59, tzinfo=pytz.timezone("US/Eastern"))

    # Price threshold to check
    price_threshold = 2.30

    # Check if the price of XRP reached the threshold
    if check_xrp_price_threshold(start_date, end_date, price_threshold):
        print("recommendation: p2")  # Yes, XRP reached $2.30 or higher
    else:
        print("recommendation: p1")  # No, XRP did not reach $2.30

if __name__ == "__main__":
    main()