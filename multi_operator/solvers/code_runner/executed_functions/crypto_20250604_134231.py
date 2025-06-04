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

def fetch_data_from_binance(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1000,  # Maximum limit
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
        print(f"Proxy failed with error: {e}, trying primary API endpoint.")
        # If proxy fails, fallback to the primary API endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def check_bitcoin_dip_to_threshold(start_date, end_date, threshold_price):
    """
    Checks if Bitcoin price dipped to or below the threshold price within the given date range.
    """
    # Convert dates to milliseconds since the epoch
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1))
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)
    
    # Fetch data
    data = fetch_data_from_binance("BTCUSDT", "1m", start_ms, end_ms)
    
    if data:
        # Check if any low price in the data dips to or below the threshold
        for candle in data:
            low_price = float(candle[3])  # Low price is the fourth element in the list
            if low_price <= threshold_price:
                return True
    return False

def main():
    # Define the date range and threshold price
    start_date = "2025-05-01"
    end_date = "2025-05-31"
    threshold_price = 75000
    
    # Check if Bitcoin dipped to or below the threshold price
    result = check_bitcoin_dip_to_threshold(start_date, end_date, threshold_price)
    
    # Print the result based on the check
    if result:
        print("recommendation: p2")  # Yes, it dipped to $75k or lower
    else:
        print("recommendation: p1")  # No, it did not dip to $75k or lower

if __name__ == "__main__":
    main()