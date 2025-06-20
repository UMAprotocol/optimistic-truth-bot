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
    Fetches data from Binance using the proxy endpoint with a fallback to the primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1000,  # Adjust based on the maximum allowed by the API
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
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def check_bitcoin_price_threshold(start_date, end_date, threshold_price):
    """
    Checks if Bitcoin price reached a certain threshold within a given date range.
    """
    # Convert dates to timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d %H:%M"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d %H:%M"))
    
    start_timestamp = int(start_dt.timestamp() * 1000)
    end_timestamp = int(end_dt.timestamp() * 1000)
    
    # Fetch data from Binance
    data = fetch_data_from_binance("BTCUSDT", "1m", start_timestamp, end_timestamp)
    
    # Check if any candle high price meets or exceeds the threshold
    for candle in data:
        high_price = float(candle[2])  # High price is at index 2
        if high_price >= threshold_price:
            return True
    return False

def main():
    """
    Main function to determine if Bitcoin reached $110K in June 2025.
    """
    result = check_bitcoin_price_threshold("2025-06-01 00:00", "2025-06-30 23:59", 110000)
    if result:
        print("recommendation: p2")  # Yes, Bitcoin reached $110K
    else:
        print("recommendation: p1")  # No, Bitcoin did not reach $110K

if __name__ == "__main__":
    main()