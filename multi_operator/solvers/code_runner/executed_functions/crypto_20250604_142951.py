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

def check_bitcoin_dip_to_50k(start_date, end_date):
    """
    Checks if Bitcoin dipped to $50k or below between the given start and end dates.
    """
    # Convert dates to UTC timestamps
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    start_utc = int(pytz.timezone("US/Eastern").localize(start_dt).timestamp() * 1000)
    end_utc = int(pytz.timezone("US/Eastern").localize(end_dt).timestamp() * 1000)

    # Fetch data from Binance
    data = fetch_data_from_binance("BTCUSDT", "1m", start_utc, end_utc)

    if data:
        # Check if any 'Low' price in the data is $50,000 or lower
        for candle in data:
            low_price = float(candle[3])
            if low_price <= 50000:
                return True
    return False

def main():
    # Define the period to check for the Bitcoin price dip
    start_date = "2025-05-01"
    end_date = "2025-05-31"

    # Check if Bitcoin dipped to $50k or below
    dipped_to_50k = check_bitcoin_dip_to_50k(start_date, end_date)

    # Print the result based on the dip status
    if dipped_to_50k:
        print("recommendation: p2")  # Yes, it dipped to $50k or below
    else:
        print("recommendation: p1")  # No, it did not dip to $50k or below

if __name__ == "__main__":
    main()