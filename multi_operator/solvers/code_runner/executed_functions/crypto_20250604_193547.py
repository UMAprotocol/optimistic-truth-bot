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
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            return None

def check_price_threshold(symbol, start_date, end_date, threshold_price):
    """
    Checks if the price of a symbol ever goes below a certain threshold between two dates.
    """
    # Convert dates to UTC timestamps
    start_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.timezone("US/Eastern")).astimezone(pytz.utc)
    end_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.timezone("US/Eastern")).astimezone(pytz.utc)
    
    start_timestamp = int(start_dt.timestamp() * 1000)
    end_timestamp = int(end_dt.timestamp() * 1000)
    
    # Fetch price data
    data = fetch_price_data(symbol, start_timestamp, end_timestamp)
    
    if data:
        # Check if any close price is below the threshold
        for candle in data:
            close_price = float(candle[4])
            if close_price <= threshold_price:
                return True
    return False

def main():
    """
    Main function to determine if the price of HYPE/USDC ever dips to $14 or below.
    """
    symbol = "HYPEUSDC"
    start_date = "2025-05-07 16:00:00"
    end_date = "2025-05-31 23:59:00"
    threshold_price = 14.0
    
    if check_price_threshold(symbol, start_date, end_date, threshold_price):
        print("recommendation: p2")  # Yes, price dipped to $14 or below
    else:
        print("recommendation: p1")  # No, price did not dip to $14 or below

if __name__ == "__main__":
    main()