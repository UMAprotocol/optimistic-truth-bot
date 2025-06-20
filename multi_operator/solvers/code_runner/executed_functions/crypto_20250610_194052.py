import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz

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
        "limit": 1000,  # Maximum limit
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
        print(f"Proxy API failed, error: {e}. Trying primary API...")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary API also failed, error: {e}")
            return None

def check_eth_price_threshold(start_date, end_date, threshold):
    """
    Checks if the Ethereum price reached a certain threshold within a given date range.
    """
    # Convert dates to timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))
    
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)
    
    # Fetch data from Binance
    data = fetch_data_from_binance("ETHUSDT", start_ts, end_ts)
    
    if data:
        # Check if any high price in the data exceeds the threshold
        for candle in data:
            high_price = float(candle[2])  # High price is the third element in each candle
            if high_price >= threshold:
                return True
    return False

def main():
    # Define the date range and threshold for the Ethereum price
    start_date = "2025-06-01"
    end_date = "2025-06-30"
    price_threshold = 2800.0
    
    # Check if the price threshold was reached
    if check_eth_price_threshold(start_date, end_date, price_threshold):
        print("recommendation: p2")  # Yes, Ethereum reached $2800
    else:
        print("recommendation: p1")  # No, Ethereum did not reach $2800

if __name__ == "__main__":
    main()