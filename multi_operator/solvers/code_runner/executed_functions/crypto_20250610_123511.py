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
PRIMARY_API_ENDPOINT = "https://api.binance.com/api/v3/klines"
PROXY_API_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_data_from_binance(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum allowed by Binance for one request
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(PROXY_API_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_ENDPOINT, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_xrp_price_threshold(start_date, end_date, threshold_price):
    """
    Checks if the XRP price reached the threshold price at any point between the start and end dates.
    """
    # Convert dates to UTC timestamps
    start_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
    start_timestamp = int(start_dt.replace(tzinfo=pytz.UTC).timestamp() * 1000)
    end_timestamp = int(end_dt.replace(tzinfo=pytz.UTC).timestamp() * 1000)

    # Fetch data from Binance
    data = fetch_data_from_binance("XRPUSDT", start_timestamp, end_timestamp)

    if data:
        # Check if any candle's high price meets or exceeds the threshold
        for candle in data:
            high_price = float(candle[2])  # High price is the third element in each candle
            if high_price >= threshold_price:
                return True
    return False

def main():
    # Define the period to check the XRP price
    start_date = "2025-06-01 00:00:00"
    end_date = "2025-06-30 23:59:59"
    threshold_price = 2.3

    # Check if the price of XRP reached the threshold
    if check_xrp_price_threshold(start_date, end_date, threshold_price):
        print("recommendation: p2")  # Yes, XRP reached $2.3
    else:
        print("recommendation: p1")  # No, XRP did not reach $2.3

if __name__ == "__main__":
    main()