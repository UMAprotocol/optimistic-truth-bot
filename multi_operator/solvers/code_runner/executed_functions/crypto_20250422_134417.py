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

def fetch_data_from_binance(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1000,  # Adjust based on the maximum allowed by the API
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
        print(f"Proxy failed with error: {e}, trying primary endpoint.")
        # If proxy fails, fallback to the primary endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            print(f"Primary endpoint also failed with error: {e}")
            return None

def check_btc_price_threshold(start_date, end_date, threshold):
    """
    Checks if the Bitcoin price reached a certain threshold within a given date range.
    """
    # Convert dates to timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))
    
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)
    
    # Fetch data
    data = fetch_data_from_binance("BTCUSDT", "1m", start_ts, end_ts)
    
    if data:
        # Check if any candle high price meets or exceeds the threshold
        for candle in data:
            high_price = float(candle[2])  # High price is the third element in each candle
            if high_price >= threshold:
                return True
    return False

def main():
    # Define the date range and price threshold
    start_date = "2025-04-01"
    end_date = "2025-04-30"
    price_threshold = 90000
    
    # Check if the price threshold was met
    result = check_btc_price_threshold(start_date, end_date, price_threshold)
    
    # Print the result based on the outcome
    if result:
        print("recommendation: p2")  # Yes, price reached $90k
    else:
        print("recommendation: p1")  # No, price did not reach $90k

if __name__ == "__main__":
    main()