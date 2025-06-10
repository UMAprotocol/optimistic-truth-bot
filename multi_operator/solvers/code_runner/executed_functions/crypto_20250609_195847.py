import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Define the API endpoints
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Define the API key environment variable names
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

def fetch_data_from_proxy(symbol, interval, start_time, end_time):
    """
    Fetch data using the proxy endpoint with fallback to the primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, timeout=10)
        response.raise_for_status()
        return response.json()

def check_bitcoin_hashprice_dip(start_date, end_date, threshold_price):
    """
    Check if the Bitcoin hashprice dipped to or below the threshold price between the start and end dates.
    """
    # Convert dates to timestamps
    tz = pytz.timezone("US/Eastern")
    start_dt = tz.localize(datetime.strptime(start_date, "%Y-%m-%d %H:%M"))
    end_dt = tz.localize(datetime.strptime(end_date, "%Y-%m-%d %H:%M"))
    start_timestamp = int(start_dt.timestamp() * 1000)
    end_timestamp = int(end_dt.timestamp() * 1000)

    # Fetch data
    data = fetch_data_from_proxy("BTCUSDT", "1d", start_timestamp, end_timestamp)

    # Check for price dip
    for entry in data:
        close_price = float(entry[4])  # Close price is the fifth element in the list
        if close_price <= threshold_price:
            return True
    return False

def main():
    # Define the time period and threshold price
    start_date = "2025-05-19 18:00"
    end_date = "2025-05-31 23:59"
    threshold_price = 52.50

    # Check if the Bitcoin hashprice dipped to or below the threshold price
    result = check_bitcoin_hashprice_dip(start_date, end_date, threshold_price)

    # Print the result
    if result:
        print("recommendation: p2")  # Yes, it dipped
    else:
        print("recommendation: p1")  # No, it did not dip

if __name__ == "__main__":
    main()