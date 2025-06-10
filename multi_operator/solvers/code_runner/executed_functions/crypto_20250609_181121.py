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
    Fetches data from Binance API with a fallback to a proxy server if the primary request fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000  # Adjust based on the maximum number of data points needed
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

def check_doge_price_dip_to_threshold(start_date, end_date, threshold):
    """
    Checks if the price of Dogecoin dipped to or below a certain threshold within a given date range.
    """
    # Convert dates to UTC timestamps
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # Include the end date fully
    start_ts = int(start_dt.replace(tzinfo=pytz.UTC).timestamp() * 1000)
    end_ts = int(end_dt.replace(tzinfo=pytz.UTC).timestamp() * 1000)

    # Fetch data from Binance
    data = fetch_data_from_binance("DOGEUSDT", "1m", start_ts, end_ts)

    if data:
        # Check if any 'low' price in the data dips to or below the threshold
        for candle in data:
            low_price = float(candle[3])  # 'low' price is the fourth element in the list
            if low_price <= threshold:
                return True
    return False

def main():
    # Define the date range and threshold for checking the Dogecoin price dip
    start_date = "2025-05-01"
    end_date = "2025-05-31"
    threshold = 0.16

    # Check if the price dipped to or below the threshold
    result = check_doge_price_dip_to_threshold(start_date, end_date, threshold)

    # Print the result based on the check
    if result:
        print("recommendation: p2")  # Yes, it dipped to $0.16 or lower
    else:
        print("recommendation: p1")  # No, it did not dip to $0.16 or lower

if __name__ == "__main__":
    main()