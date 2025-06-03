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
    Fetches data from Binance API with a fallback to a proxy server if the primary request fails.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum allowed by Binance for one request
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try fetching data using the proxy URL first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy request failed, trying primary API. Error: {e}")

    try:
        # Fallback to the primary API if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Both proxy and primary API requests failed. Error: {e}")
        return None

def check_xrp_price_threshold(start_date, end_date, threshold=2.2):
    """
    Checks if the XRP price reaches or exceeds the threshold at any point between the start and end dates.
    """
    # Convert dates to UTC timestamps
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(start_dt).astimezone(pytz.utc)
    end_dt = tz.localize(end_dt).astimezone(pytz.utc)

    # Convert datetime to milliseconds since epoch
    start_time = int(start_dt.timestamp() * 1000)
    end_time = int(end_dt.timestamp() * 1000)

    # Fetch data from Binance
    data = fetch_data_from_binance("XRPUSDT", start_time, end_time)

    if data:
        # Check if any 'High' price in the data exceeds the threshold
        for candle in data:
            high_price = float(candle[2])  # 'High' price is at index 2
            if high_price >= threshold:
                return True
    return False

def main():
    # Define the period to check the XRP price
    start_date = "2025-06-01"
    end_date = "2025-06-30"

    # Check if the price of XRP reaches $2.2 or higher
    if check_xrp_price_threshold(start_date, end_date):
        print("recommendation: p2")  # Yes, it reached $2.2 or higher
    else:
        print("recommendation: p1")  # No, it did not reach $2.2

if __name__ == "__main__":
    main()