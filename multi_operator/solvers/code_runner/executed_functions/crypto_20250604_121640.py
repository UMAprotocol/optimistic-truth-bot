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

def fetch_data_from_binance(symbol, start_time, end_time):
    """
    Fetches cryptocurrency data from Binance using the proxy endpoint with a fallback to the primary endpoint.
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
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def check_sui_price_threshold(start_date, end_date, threshold_price):
    """
    Checks if the SUI/USDT price reached the threshold price within the given date range.
    """
    # Convert dates to timestamps
    start_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
    start_timestamp = int(start_dt.timestamp() * 1000)  # Convert to milliseconds
    end_timestamp = int(end_dt.timestamp() * 1000)  # Convert to milliseconds

    # Fetch data from Binance
    data = fetch_data_from_binance("SUIUSDT", start_timestamp, end_timestamp)

    if data:
        # Check if any candle's high price meets or exceeds the threshold
        for candle in data:
            high_price = float(candle[2])  # High price is at index 2
            if high_price >= threshold_price:
                return True
    return False

def main():
    # Define the date range and threshold price
    start_date = "2025-05-07 00:00:00"
    end_date = "2025-05-31 23:59:59"
    threshold_price = 4.4

    # Check if the price threshold was reached
    result = check_sui_price_threshold(start_date, end_date, threshold_price)

    # Print the result based on the outcome
    if result:
        print("recommendation: p2")  # Yes, price reached $4.4 or higher
    else:
        print("recommendation: p1")  # No, price did not reach $4.4

if __name__ == "__main__":
    main()