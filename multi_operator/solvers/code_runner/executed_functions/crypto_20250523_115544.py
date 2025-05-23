import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Define the API endpoints
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

# Define the symbol and the threshold price
SYMBOL = "HYPEUSDC"
THRESHOLD_PRICE = 35.0

# Define the time range
START_DATE = "2025-05-07 16:00:00"
END_DATE = "2025-05-31 23:59:00"
TIMEZONE = "US/Eastern"

def fetch_data(symbol, start_time, end_time):
    """
    Fetches data from the Binance API using a proxy and falls back to the primary endpoint if necessary.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Adjust based on the maximum allowed by the API
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data using the proxy URL
        response = requests.get(PROXY_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Proxy failed, trying primary endpoint: {e}")
        # Fallback to the primary URL if proxy fails
        response = requests.get(f"{PRIMARY_URL}/klines", params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def check_price_threshold(data):
    """
    Checks if any 'High' price in the data exceeds the threshold price.
    """
    for candle in data:
        high_price = float(candle[2])  # 'High' price is at index 2 in each candle
        if high_price >= THRESHOLD_PRICE:
            return True
    return False

def main():
    # Convert the start and end dates to UTC timestamps
    tz = pytz.timezone(TIMEZONE)
    start_dt = tz.localize(datetime.strptime(START_DATE, "%Y-%m-%d %H:%M:%S")).astimezone(pytz.utc)
    end_dt = tz.localize(datetime.strptime(END_DATE, "%Y-%m-%d %H:%M:%S")).astimezone(pytz.utc)
    
    start_timestamp = int(start_dt.timestamp() * 1000)  # Convert to milliseconds
    end_timestamp = int(end_dt.timestamp() * 1000)      # Convert to milliseconds
    
    # Fetch the data
    data = fetch_data(SYMBOL, start_timestamp, end_timestamp)
    
    # Check if the price threshold was reached
    if check_price_threshold(data):
        print("recommendation: p2")  # Yes, price reached $35 or higher
    else:
        print("recommendation: p1")  # No, price did not reach $35

if __name__ == "__main__":
    main()