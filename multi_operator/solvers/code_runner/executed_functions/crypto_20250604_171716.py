import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_data_from_binance(symbol, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1000,  # Maximum allowed by Binance for one request
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

def check_solana_price_threshold(start_date, end_date, threshold):
    """
    Checks if Solana's price reached a certain threshold between two dates.
    """
    # Convert dates to UTC timestamps
    start_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
    start_timestamp = int(start_dt.replace(tzinfo=pytz.UTC).timestamp() * 1000)
    end_timestamp = int(end_dt.replace(tzinfo=pytz.UTC).timestamp() * 1000)

    # Fetch data from Binance
    data = fetch_data_from_binance("SOLUSDT", start_timestamp, end_timestamp)

    if data:
        # Check if any candle's high price meets or exceeds the threshold
        for candle in data:
            high_price = float(candle[2])  # High price is the third element in the list
            if high_price >= threshold:
                return True
    return False

def main():
    # Define the period to check
    start_date = "2025-05-01 00:00:00"
    end_date = "2025-05-31 23:59:59"
    threshold_price = 250.00

    # Check if Solana reached the price threshold
    result = check_solana_price_threshold(start_date, end_date, threshold_price)

    # Print the result based on the check
    if result:
        print("recommendation: p2")  # Yes, Solana reached $250 or higher
    else:
        print("recommendation: p1")  # No, Solana did not reach $250

if __name__ == "__main__":
    main()