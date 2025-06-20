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

def fetch_data_from_binance(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000  # Adjust based on the maximum results needed per API call
    }
    
    try:
        # Try fetching data using the proxy URL first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy failed with error {e}, trying primary API endpoint.")
        try:
            # Fallback to the primary API endpoint if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary API also failed with error {e}.")
            return None

def check_bitcoin_price_threshold(start_date, end_date, threshold):
    """
    Checks if Bitcoin price reached a certain threshold within a given date range.
    """
    # Convert dates to UTC timestamps
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # Include the end date fully
    start_ts = int(start_dt.replace(tzinfo=pytz.UTC).timestamp() * 1000)
    end_ts = int(end_dt.replace(tzinfo=pytz.UTC).timestamp() * 1000)

    # Fetch data from Binance
    data = fetch_data_from_binance("BTCUSDT", "1m", start_ts, end_ts)

    if data:
        # Check if any candle high price meets or exceeds the threshold
        for candle in data:
            high_price = float(candle[2])  # High price is at index 2 in each candle
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

    # Print the result based on the check
    if result:
        print("recommendation: p2")  # Yes, Bitcoin reached $110K
    else:
        print("recommendation: p1")  # No, Bitcoin did not reach $110K

if __name__ == "__main__":
    main()