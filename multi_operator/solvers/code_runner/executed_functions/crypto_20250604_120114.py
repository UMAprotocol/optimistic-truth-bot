import requests
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_data_from_binance(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum allowed by Binance
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try fetching data from the proxy endpoint first
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
    Checks if any 'High' price in the data exceeds the threshold.
    """
    for candle in data:
        high_price = float(candle[2])  # 'High' price is the third item in the list
        if high_price >= threshold:
            return True
    return False

def main():
    # Define the symbol and threshold based on the market question
    symbol = "SUIUSDT"
    threshold = 4.8
    start_date = datetime(2025, 5, 7, 0, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_date = datetime(2025, 5, 31, 23, 59, 59, tzinfo=pytz.timezone("US/Eastern"))

    # Convert dates to UTC timestamps in milliseconds
    start_time = int(start_date.astimezone(pytz.utc).timestamp() * 1000)
    end_time = int(end_date.astimezone(pytz.utc).timestamp() * 1000)

    # Fetch data from Binance
    data = fetch_data_from_binance(symbol, start_time, end_time)

    if data:
        # Check if the price threshold was ever met
        if check_price_threshold(data, threshold):
            print("recommendation: p2")  # Yes, price reached the threshold
        else:
            print("recommendation: p1")  # No, price did not reach the threshold
    else:
        print("recommendation: p3")  # Unknown or data fetch error

if __name__ == "__main__":
    main()