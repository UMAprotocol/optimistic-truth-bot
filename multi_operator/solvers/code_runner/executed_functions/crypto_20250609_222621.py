import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

def get_data(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint.
    """
    try:
        # First try the proxy endpoint
        response = requests.get(f"{PROXY_URL}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            return data[0][4]  # Close price of the candle
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_URL}/klines", params={
            "symbol": symbol,
            "interval": "1m",
            "limit": 1,
            "startTime": start_time,
            "endTime": end_time
        }, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            return data[0][4]  # Close price of the candle

def check_fartcoin_price():
    """
    Checks if Fartcoin dipped to $0.20 or lower between specified dates.
    """
    # Define the time range
    start_date = datetime(2025, 5, 7, 15, 0, tzinfo=pytz.timezone('US/Eastern'))
    end_date = datetime(2025, 5, 31, 23, 59, tzinfo=pytz.timezone('US/Eastern'))
    
    # Convert to milliseconds since this is what Binance API expects
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)
    
    # Symbol for Fartcoin traded against SOL on Binance
    symbol = "FARTSOL"

    # Check prices within the range
    try:
        price = get_data(symbol, start_time, end_time)
        if price is not None and float(price) <= 0.20:
            return "recommendation: p2"  # Yes, it dipped to $0.20 or lower
        else:
            return "recommendation: p1"  # No, it did not dip to $0.20 or lower
    except Exception as e:
        print(f"Error fetching data: {e}")
        return "recommendation: p3"  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    result = check_fartcoin_price()
    print(result)