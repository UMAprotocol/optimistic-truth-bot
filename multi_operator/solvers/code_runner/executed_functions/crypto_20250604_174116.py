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
            return data[0][3]  # Low price
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
            return data[0][3]  # Low price
    return None

def check_price_dip(symbol, start_date, end_date, target_price):
    """
    Checks if the price of a cryptocurrency dipped to or below a target price between two dates.
    """
    # Convert dates to timestamps
    start_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M")
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)

    # Check prices over the range
    while start_ts < end_ts:
        low_price = get_data(symbol, start_ts, start_ts + 60000)  # Check each minute
        if low_price is not None and float(low_price) <= target_price:
            return True
        start_ts += 60000  # Move to the next minute

    return False

def main():
    # Example parameters
    symbol = "FARTCOINSOL"
    start_date = "2025-05-07 15:00"
    end_date = "2025-05-31 23:59"
    target_price = 0.90

    # Check if the price dipped to or below the target price
    if check_price_dip(symbol, start_date, end_date, target_price):
        print("recommendation: p2")  # Yes, it dipped
    else:
        print("recommendation: p1")  # No, it did not dip

if __name__ == "__main__":
    main()