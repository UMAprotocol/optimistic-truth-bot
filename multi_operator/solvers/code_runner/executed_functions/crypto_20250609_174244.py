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

def fetch_price_data(symbol, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            return float(data[0][2])  # High price from the candle
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary API.")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data and len(data) > 0:
                return float(data[0][2])  # High price from the candle
        except Exception as e:
            print(f"Primary API failed with error: {e}")
            return None

def check_fartcoin_price():
    """
    Checks if Fartcoin reached $2.00 at any point between the specified dates.
    """
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone("US/Eastern"))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone("US/Eastern"))
    
    # Convert to UTC timestamps
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)
    
    # Check prices in intervals (due to API limitations, check daily)
    current_time = start_timestamp
    while current_time <= end_timestamp:
        high_price = fetch_price_data("FARTCOINSOL", current_time, current_time + 60000)  # 1 minute in milliseconds
        if high_price is not None and high_price >= 2.00:
            return "p2"  # Yes, Fartcoin reached $2.00
        current_time += 86400000  # Move to the next day
    
    return "p1"  # No, Fartcoin did not reach $2.00

def main():
    result = check_fartcoin_price()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()