import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API for a given symbol within a specified time range.
    Implements a fallback mechanism from proxy to primary API endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum limit
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint
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

def check_price_threshold(data, threshold):
    """
    Checks if any 'High' price in the data exceeds the given threshold.
    """
    for candle in data:
        if float(candle[2]) >= threshold:  # 'High' price is at index 2
            return True
    return False

def main():
    # Define the symbol and threshold based on the market question
    symbol = "SOLUSDT"
    threshold = 160.0
    start_date = datetime(2025, 6, 1, 0, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_date = datetime(2025, 6, 30, 23, 59, 59, tzinfo=pytz.timezone("US/Eastern"))
    
    # Convert datetime to milliseconds since epoch
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)
    
    # Fetch price data
    data = fetch_price_data(symbol, start_time, end_time)
    
    if data:
        # Check if the price ever reaches or exceeds the threshold
        if check_price_threshold(data, threshold):
            print("recommendation: p2")  # Yes, price reached the threshold
        else:
            print("recommendation: p1")  # No, price did not reach the threshold
    else:
        print("recommendation: p3")  # Unknown or data fetch error

if __name__ == "__main__":
    main()