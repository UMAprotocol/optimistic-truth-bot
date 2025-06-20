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

def fetch_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1000,  # Maximum allowed by Binance
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data using the proxy API first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy API failed, trying primary API. Error: {e}")
        # If proxy fails, fallback to the primary API
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Both proxy and primary API requests failed. Error: {e}")
            return None

def check_bitcoin_price_threshold(start_date, end_date, threshold):
    """
    Checks if Bitcoin price reached a certain threshold within a given date range.
    """
    # Convert dates to timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))
    
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)
    
    # Fetch data
    data = fetch_data("BTCUSDT", "1m", start_ts, end_ts)
    
    if data:
        for candle in data:
            high_price = float(candle[2])  # High price is the third element in the list
            if high_price >= threshold:
                return True
    return False

def main():
    # Define the date range and price threshold
    start_date = "2025-06-01"
    end_date = "2025-06-30"
    price_threshold = 110000
    
    # Check if Bitcoin reached the price threshold
    result = check_bitcoin_price_threshold(start_date, end_date, price_threshold)
    
    # Print the result based on the outcome
    if result:
        print("recommendation: p2")  # Yes, Bitcoin reached $110K
    else:
        print("recommendation: p1")  # No, Bitcoin did not reach $110K

if __name__ == "__main__":
    main()